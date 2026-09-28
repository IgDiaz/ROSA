# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Scoped, persistent observations. Only trusted sensor adapters write facts."""
from contextlib import contextmanager
from dataclasses import dataclass
import json
import math
import re
import sqlite3
import threading
import time

DESTINATIONS = ("base", "linea_1", "linea_2", "almacen")
CAPABILITIES = ("navigate", "inspect", "dock", "hold", "report")
TTL = {"battery": 10, "obstacle": 3, "estop": 3, "position": 10}


@dataclass(frozen=True)
class Scope:
    user_id: str
    robot_id: str

    def __post_init__(self):
        for value in (self.user_id, self.robot_id):
            if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", value):
                raise ValueError("Identidad inválida")

    @property
    def key(self):
        return self.user_id, self.robot_id


def validate_fact(key, value):
    if key == "battery":
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError("La batería debe estar entre 0 y 100")
    elif key in ("obstacle", "estop"):
        if type(value) is not bool:
            raise ValueError("El sensor requiere un booleano")
    elif key == "position":
        if value not in DESTINATIONS:
            raise ValueError("Posición fuera del mapa registrado")
    else:
        raise ValueError("Dato no registrado en el perfil")


class ContextStore:
    def __init__(self, path=":memory:", clock=time.time):
        self.clock = clock
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS robots(
          user_id TEXT, robot_id TEXT, mode TEXT, revision INTEGER DEFAULT 0,
          capabilities TEXT, PRIMARY KEY(user_id,robot_id));
        CREATE TABLE IF NOT EXISTS facts(
          user_id TEXT, robot_id TEXT, name TEXT, value TEXT, source TEXT,
          confidence REAL, observed_at REAL, PRIMARY KEY(user_id,robot_id,name));
        CREATE TABLE IF NOT EXISTS plans(
          id TEXT PRIMARY KEY, user_id TEXT, robot_id TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS events(
          sequence INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, robot_id TEXT,
          at REAL, kind TEXT, data TEXT);
        """)

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                self.db.execute("ROLLBACK")
                raise
            else:
                self.db.execute("COMMIT")

    def register(self, scope, mode="simulation", capabilities=CAPABILITIES):
        if mode not in ("simulation", "observation") or not set(capabilities) <= set(CAPABILITIES):
            raise ValueError("Perfil inválido")
        with self.transaction():
            self.db.execute("INSERT OR IGNORE INTO robots VALUES(?,?,?,0,?)",
                            (*scope.key, mode, json.dumps(list(capabilities))))

    def robot(self, scope):
        with self.lock:
            row = self.db.execute("SELECT * FROM robots WHERE user_id=? AND robot_id=?", scope.key).fetchone()
            if not row:
                raise ValueError("Robot no registrado en este espacio")
            return dict(row)

    def observe(self, scope, values, source, confidence=1.0, observed_at=None):
        if not isinstance(source, str) or not 1 <= len(source) <= 120:
            raise ValueError("Fuente requerida")
        if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Confianza inválida")
        at = self.clock() if observed_at is None else observed_at
        if type(at) not in (int, float) or not math.isfinite(at) or at > self.clock() + 1:
            raise ValueError("Fecha inválida o futura")
        for key, value in values.items():
            validate_fact(key, value)
        with self.transaction():
            self.robot(scope)
            self._observe(scope, values, source, confidence, at)

    def _observe(self, scope, values, source, confidence, at):
        """Caller holds a transaction; also used by the simulator atomically."""
        changed = False
        for name, value in values.items():
            previous = self.db.execute("SELECT * FROM facts WHERE user_id=? AND robot_id=? AND name=?",
                                       (*scope.key, name)).fetchone()
            if previous and at < previous["observed_at"]:
                continue
            encoded = json.dumps(value, allow_nan=False)
            if not previous or (previous["value"], previous["source"], previous["confidence"]) != (encoded, source, confidence):
                changed = True
            self.db.execute("INSERT OR REPLACE INTO facts VALUES(?,?,?,?,?,?,?)",
                            (*scope.key, name, encoded, source, confidence, at))
        if changed:
            self.db.execute("UPDATE robots SET revision=revision+1 WHERE user_id=? AND robot_id=?", scope.key)

    def snapshot(self, scope):
        with self.lock:
            # A single SQL statement keeps revision and facts consistent even
            # if a ROS observer writes through a separate connection/process.
            rows = list(self.db.execute("""SELECT r.mode, r.revision, r.capabilities,
                f.name, f.value, f.source, f.confidence, f.observed_at
                FROM robots r LEFT JOIN facts f
                ON r.user_id=f.user_id AND r.robot_id=f.robot_id
                WHERE r.user_id=? AND r.robot_id=?""", scope.key))
            if not rows:
                raise ValueError("Robot no registrado en este espacio")
            robot = rows[0]
            now = self.clock()
            facts = {}
            for row in rows:
                if row["name"] is None:
                    continue
                age = now - row["observed_at"]
                facts[row["name"]] = {"value": json.loads(row["value"]), "source": row["source"],
                    "confidence": row["confidence"], "observed_at": row["observed_at"],
                    "age_s": round(age, 2), "fresh": 0 <= age <= TTL[row["name"]]}
            return {"schema_version": "1.0", "user_id": scope.user_id, "robot_id": scope.robot_id,
                    "mode": robot["mode"], "revision": robot["revision"], "at": now,
                    "capabilities": json.loads(robot["capabilities"]), "facts": facts}

    def event(self, scope, kind, data):
        with self.lock:
            self.db.execute("INSERT INTO events(user_id,robot_id,at,kind,data) VALUES(?,?,?,?,?)",
                            (*scope.key, self.clock(), kind, json.dumps(data, ensure_ascii=False)))

    def history(self, scope, limit=30):
        with self.lock:
            return [{"sequence": r["sequence"], "at": r["at"], "kind": r["kind"], "data": json.loads(r["data"])}
                    for r in self.db.execute("SELECT * FROM events WHERE user_id=? AND robot_id=? ORDER BY sequence DESC LIMIT ?",
                                             (*scope.key, min(max(int(limit), 1), 200)))]

    def save_plan(self, scope, plan):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO plans VALUES(?,?,?,?)",
                            (plan["id"], *scope.key, json.dumps(plan, ensure_ascii=False)))

    def load_plan(self, scope, plan_id):
        with self.lock:
            row = self.db.execute("SELECT data FROM plans WHERE id=? AND user_id=? AND robot_id=?",
                                  (plan_id, *scope.key)).fetchone()
            if not row:
                raise ValueError("Propuesta no encontrada en este espacio")
            return json.loads(row["data"])

    def close(self):
        self.db.close()
