# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Loopback-only demonstration console. Not a production HTTP server."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import secrets
import threading
from .context import ContextStore, Scope
from .runtime import Runtime
from .planner import OllamaPlanner, RulesPlanner
from .gateway import context_envelope


class Demo:
    def __init__(self, db=":memory:", model=None, start_heartbeat=True):
        self.store = ContextStore(db)
        self.scope = Scope("demo", "amr_01")
        self.store.register(self.scope)
        if self.store.robot(self.scope)["mode"] != "simulation":
            raise ValueError("La consola requiere un perfil de simulación")
        self.rules = Runtime(self.store, RulesPlanner())
        self.local = Runtime(self.store, OllamaPlanner(model)) if model else None
        self.paused, self.scene = False, "normal"
        self.stop = threading.Event()
        self.scenario("normal")
        self.thread = None
        if start_heartbeat:
            self.thread = threading.Thread(target=self.heartbeat, daemon=True)
            self.thread.start()

    def heartbeat(self):
        while not self.stop.wait(0.5):
            self.refresh_telemetry()

    def refresh_telemetry(self):
        """Sample the virtual sensors; paused scenes intentionally age out."""
        with self.store.lock:
            if not self.paused:
                values = {k: v["value"] for k, v in self.store.snapshot(self.scope)["facts"].items()}
                self.store.observe(self.scope, values, "simulator")

    def scenario(self, name):
        if name not in ("normal", "battery", "obstacle", "estop", "offline"):
            raise ValueError("Escenario desconocido")
        with self.store.lock:
            self.scene, self.paused = name, name == "offline"
            if not self.paused:
                self.store.observe(self.scope, {"battery": 14 if name == "battery" else 82,
                    "obstacle": name == "obstacle", "estop": name == "estop", "position": "base"}, "simulator")
            self.store.event(self.scope, "scenario", {"name": name, "simulation": True})

    def state(self):
        return {"context": self.store.snapshot(self.scope), "history": self.store.history(self.scope),
                "scene": self.scene, "model": self.local.planner.model if self.local else None}

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=2)
        self.store.close()


def make_server(demo, port):
    token = secrets.token_urlsafe(32)
    html = (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8").replace("__ROSA_TOKEN__", token)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def allowed_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

        def reply(self, status, body, content_type="application/json"):
            data = body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.allowed_host():
                return self.reply(403, {"error": "Host no permitido"})
            if self.path == "/":
                return self.reply(200, html, "text/html")
            if self.path == "/favicon.svg":
                icon = (Path(__file__).parent / "web" / "favicon.svg").read_text(encoding="utf-8")
                return self.reply(200, icon, "image/svg+xml")
            if self.path == "/api/state":
                return self.reply(200, demo.state())
            if self.path == "/api/export":
                return self.reply(200, context_envelope(demo.store.snapshot(demo.scope)))
            self.reply(404, {"error": "Ruta no encontrada"})

        def do_POST(self):
            origin = self.headers.get("Origin")
            valid_origin = origin is None or origin == "http://" + self.headers.get("Host", "")
            if not self.allowed_host() or not valid_origin or not secrets.compare_digest(self.headers.get("X-ROSA-Token", ""), token):
                return self.reply(403, {"error": "Solicitud no autorizada"})
            try:
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("Se requiere application/json")
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 8192:
                    raise ValueError("Tamaño inválido")
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("Se requiere un objeto JSON")
                if self.path == "/api/scenario":
                    demo.scenario(body.get("name"))
                    return self.reply(200, demo.state())
                if self.path == "/api/plan":
                    provider = body.get("provider", "rules")
                    if provider not in ("rules", "ollama"):
                        raise ValueError("Proveedor inválido")
                    runtime = demo.local if provider == "ollama" else demo.rules
                    if runtime is None:
                        raise ValueError("Inicia ROSA con --ollama-model MODELO_LOCAL para habilitar Ollama")
                    return self.reply(200, runtime.propose(demo.scope, body.get("text")))
                if self.path == "/api/execute":
                    if not isinstance(body.get("id"), str):
                        raise ValueError("Identificador requerido")
                    return self.reply(200, demo.rules.execute_simulation(demo.scope, body["id"]))
                return self.reply(404, {"error": "Ruta no encontrada"})
            except (ValueError, TypeError, KeyError):
                # Detailed actionable validation messages, but no network internals or credentials.
                import sys
                exc = sys.exception()
                return self.reply(400, {"error": str(exc) if isinstance(exc, ValueError) else "Formato inválido"})
            except Exception:
                return self.reply(502, {"error": "No fue posible completar la solicitud. Verifica el servicio local y el modelo instalado."})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765, db="rosa-demo.sqlite3", model=None):
    demo = Demo(db, model)
    server = make_server(demo, port)
    print(f"ROSA · simulación local · http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        demo.close()
