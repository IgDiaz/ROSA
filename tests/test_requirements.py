"""Regression scenarios for operating requirements and trusted observation age."""
import json
import sqlite3
import tempfile
import threading
import unittest
from dataclasses import replace
from rosa import ContextStore, OperationalProfile, Runtime, Scope, ingest_telemetry


class RequirementsTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        self.store = ContextStore(clock=lambda: self.now)
        self.scope = Scope("plant", "amr")
        self.store.register(self.scope)
        self.values = {"battery": 82, "obstacle": False, "estop": False, "position": "base"}
        self.store.observe(self.scope, self.values, "sensor")
        self.runtime = Runtime(self.store)

    def tearDown(self):
        self.store.close()

    def test_requirements_change_decision_and_persist_in_proposal(self):
        self.store.configure(self.scope, OperationalProfile(minimum_battery=90, proposal_ttl_s=5))
        plan = self.runtime.propose(self.scope, "inspect line 2")
        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["profile"]["minimum_battery"], 90)
        self.assertEqual(plan["expires_at"], 1005)

    def test_profile_update_invalidates_old_proposal(self):
        plan = self.runtime.propose(self.scope, "inspect line 2")
        self.store.configure(self.scope, OperationalProfile(minimum_battery=90))
        with self.assertRaisesRegex(ValueError, "contexto cambió"):
            self.runtime.execute_simulation(self.scope, plan["id"])

    def test_identical_profile_update_preserves_proposal(self):
        plan = self.runtime.propose(self.scope, "inspect line 2")
        self.store.configure(self.scope, OperationalProfile())
        self.assertEqual(self.runtime.execute_simulation(self.scope, plan["id"])["status"], "executed_simulation")

    def test_custom_ttl_expires_evidence(self):
        self.store.configure(self.scope, OperationalProfile(obstacle_ttl_s=.1))
        self.now += .2
        self.assertEqual(self.runtime.propose(self.scope, "inspect line 2")["status"], "blocked")

    def test_source_allowlist_rejects_write_and_existing_untrusted_evidence(self):
        self.store.configure(self.scope, OperationalProfile(allowed_sources=("certified-adapter",)))
        with self.assertRaisesRegex(ValueError, "Fuente"):
            self.store.observe(self.scope, self.values, "sensor")
        self.assertEqual(self.runtime.propose(self.scope, "inspect line 2")["status"], "blocked")

    def test_acquisition_requirement_applies_to_existing_evidence(self):
        self.store.configure(self.scope, OperationalProfile(require_acquisition_time=True))
        with self.assertRaisesRegex(ValueError, "adquisición"):
            self.store.observe(self.scope, self.values, "sensor")
        self.assertEqual(self.runtime.propose(self.scope, "inspect line 2")["status"], "blocked")
        self.store.observe(self.scope, self.values, "sensor", observed_at=self.now)
        self.assertEqual(self.runtime.propose(self.scope, "inspect line 2")["status"], "ready")

    def test_delayed_delivery_does_not_refresh_acquisition_time(self):
        self.now += 20
        self.store.observe(self.scope, self.values, "sensor", observed_at=1001, sequence=1)
        fact = self.store.snapshot(self.scope)["facts"]["obstacle"]
        self.assertEqual(fact["received_at"], 1020)
        self.assertEqual(fact["observed_at"], 1001)
        self.assertFalse(fact["fresh"])

    def test_replayed_sequence_cannot_erase_obstacle_or_refresh_age(self):
        self.store.observe(self.scope, {"obstacle": True}, "sensor", observed_at=1000, sequence=4)
        self.now += 4
        for seq in (3, 4, None):
            self.store.observe(self.scope, {"obstacle": False}, "sensor", observed_at=self.now, sequence=seq)
        fact = self.store.snapshot(self.scope)["facts"]["obstacle"]
        self.assertTrue(fact["value"])
        self.assertEqual(fact["observed_at"], 1000)
        self.assertFalse(fact["fresh"])

    def test_new_sequence_preserves_heartbeat_revision(self):
        self.store.observe(self.scope, self.values, "sensor", observed_at=1000, sequence=1)
        revision = self.store.snapshot(self.scope)["revision"]
        self.now += 1
        self.store.observe(self.scope, self.values, "sensor", observed_at=1001, sequence=2)
        self.assertEqual(self.store.snapshot(self.scope)["revision"], revision)

    def test_invalid_contracts_are_atomic(self):
        for kwargs in ({"observed_at": -1}, {"observed_at": 1000.1}, {"sequence": True},
                       {"sequence": -1}, {"sequence": 2**63}, {"observed_at": float("nan")}):
            with self.assertRaises(ValueError):
                self.store.observe(self.scope, {"battery": 20}, "sensor", **kwargs)
        for values in ({}, [], None):
            with self.assertRaises(ValueError):
                self.store.observe(self.scope, values, "sensor")
        self.assertEqual(self.store.snapshot(self.scope)["facts"]["battery"]["value"], 82)

    def packet(self, **overrides):
        return json.dumps({"schema_version": "1.0", "user_id": "plant", "robot_id": "amr",
                           "observed_at": self.now, "sequence": 1, "values": self.values, **overrides})

    def test_stamped_telemetry_contract(self):
        ingest_telemetry(self.store, self.scope, self.packet())
        fact = self.store.snapshot(self.scope)["facts"]["battery"]
        self.assertEqual((fact["source"], fact["timestamp_kind"], fact["sequence"]), ("ros2/telemetry", "acquired", 1))

    def test_telemetry_cannot_choose_scope_source_or_invalid_format(self):
        for packet in (self.packet(robot_id="other"), self.packet(source="trusted"),
                       self.packet(sequence=None), self.packet(observed_at=None),
                       self.packet(schema_version="2"), "[]", "{", " " * 8193, None):
            with self.assertRaises(ValueError):
                ingest_telemetry(self.store, self.scope, packet)

    def test_context_change_during_interpretation_blocks_proposal(self):
        store, scope, values = self.store, self.scope, self.values
        class DelayedPlanner:
            name = "delayed"
            def propose(self, text, snapshot):
                store.observe(scope, {**values, "obstacle": True}, "sensor")
                return {"action": "inspect", "target": "linea_2"}
        self.assertEqual(Runtime(store, DelayedPlanner()).propose(scope, "inspect line 2")["status"], "blocked")

    def test_evidence_expiring_during_interpretation_blocks_proposal(self):
        case = self
        class DelayedPlanner:
            name = "delayed"
            def propose(self, text, snapshot):
                case.now += 4
                return {"action": "inspect", "target": "linea_2"}
        self.assertEqual(Runtime(self.store, DelayedPlanner()).propose(self.scope, "inspect line 2")["status"], "blocked")

    def test_clock_rollback_cannot_execute_old_proposal(self):
        plan = self.runtime.propose(self.scope, "status")
        self.now -= 1
        with self.assertRaisesRegex(ValueError, "venció"):
            self.runtime.execute_simulation(self.scope, plan["id"])


class ProfileValidationTests(unittest.TestCase):
    def test_invalid_requirements_rejected(self):
        for kwargs in ({"minimum_battery": 101}, {"docking_battery": 40}, {"minimum_confidence": False},
                       {"obstacle_ttl_s": 0}, {"proposal_ttl_s": float("inf")},
                       {"require_acquisition_time": "yes"}, {"allowed_sources": ("a", "a")},
                       {"allowed_sources": ("",)}, {"allowed_sources": "a"}):
            with self.assertRaises(ValueError):
                OperationalProfile(**kwargs)

    def test_unknown_requirements_and_source_type_rejected(self):
        for data in ({"ignore_estop": True}, {"allowed_sources": "a"}, []):
            with self.assertRaises(ValueError):
                OperationalProfile.from_dict(data)

    def test_profile_json_roundtrip(self):
        profile = OperationalProfile(allowed_sources=("a",), minimum_battery=40)
        self.assertEqual(OperationalProfile.from_dict(json.loads(json.dumps(profile.to_dict()))), profile)


class DatabaseRobustnessTests(unittest.TestCase):
    def test_legacy_database_migrates_without_losing_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            path = d + "/legacy.db"
            db = sqlite3.connect(path)
            db.executescript('''CREATE TABLE robots(user_id TEXT, robot_id TEXT, mode TEXT,
                revision INTEGER DEFAULT 0, capabilities TEXT, PRIMARY KEY(user_id,robot_id));
                CREATE TABLE facts(user_id TEXT, robot_id TEXT, name TEXT, value TEXT, source TEXT,
                confidence REAL, observed_at REAL, PRIMARY KEY(user_id,robot_id,name));
                INSERT INTO robots VALUES('p','r','observation',3,'["report"]');
                INSERT INTO facts VALUES('p','r','battery','80','old-sensor',1,1000);''')
            db.close()
            store = ContextStore(path, clock=lambda: 1001)
            try:
                snap = store.snapshot(Scope("p", "r"))
                self.assertEqual(snap["revision"], 3)
                self.assertEqual(snap["facts"]["battery"]["value"], 80)
                self.assertEqual(snap["facts"]["battery"]["timestamp_kind"], "received")
            finally:
                store.close()

    def test_profile_and_sequence_survive_reopen(self):
        with tempfile.TemporaryDirectory() as d:
            scope, path = Scope("p", "r"), d + "/context.db"
            store = ContextStore(path, clock=lambda: 1000)
            profile = OperationalProfile(require_acquisition_time=True)
            store.register(scope, profile=profile)
            store.observe(scope, {"obstacle": True}, "sensor", observed_at=1000, sequence=9)
            store.close()
            store = ContextStore(path, clock=lambda: 1001)
            try:
                self.assertEqual(store.profile(scope), profile)
                store.observe(scope, {"obstacle": False}, "sensor", observed_at=1001, sequence=9)
                self.assertTrue(store.snapshot(scope)["facts"]["obstacle"]["value"])
            finally:
                store.close()

    def test_concurrent_confirmation_has_one_effect(self):
        with tempfile.TemporaryDirectory() as d:
            scope, path = Scope("p", "r"), d + "/concurrent.db"
            first, second = ContextStore(path), ContextStore(path)
            first.register(scope)
            first.observe(scope, {"battery": 82, "obstacle": False, "estop": False, "position": "base"}, "simulator")
            plan = Runtime(first).propose(scope, "inspect line 2")
            barrier, results, errors = threading.Barrier(2), [], []
            def confirm(store):
                try:
                    barrier.wait(timeout=5)
                    results.append(Runtime(store).execute_simulation(scope, plan["id"]))
                except Exception as exc:
                    errors.append(exc)
            threads = [threading.Thread(target=confirm, args=(s,)) for s in (first, second)]
            try:
                for thread in threads:thread.start()
                for thread in threads:thread.join(timeout=10)
                self.assertFalse(any(t.is_alive() for t in threads))
                self.assertEqual(errors, [])
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0], results[1])
                self.assertEqual(first.snapshot(scope)["facts"]["battery"]["value"], 79)
            finally:
                first.close();second.close()


if __name__ == "__main__":
    unittest.main()
