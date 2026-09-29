# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Propose, check, explicitly confirm, and apply simulation effects only."""
import uuid
from .planner import RulesPlanner
from .policy import assess, validate_intent


class Runtime:
    def __init__(self, store, planner=None):
        self.store = store
        self.planner = planner or RulesPlanner()

    def propose(self, scope, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError("Escribe una orden de 1 a 2000 caracteres")
        snapshot = self.store.snapshot(scope)
        # Historical text is advisory context, never a substitute for live facts.
        planner_context = {**snapshot, "recent_events": self.store.history(scope, 5)}
        intent = validate_intent(self.planner.propose(text, planner_context))
        planning_revision = snapshot["revision"]
        # A local model can take seconds. Re-read evidence after interpretation;
        # reject intents interpreted against a different semantic context.
        snapshot = self.store.snapshot(scope)
        status, reason = assess(snapshot, intent)
        if snapshot["revision"] != planning_revision:
            status, reason = "blocked", "El contexto cambió durante la interpretación. Genera una nueva propuesta."
        plan = {"id": str(uuid.uuid4()), "request": text, "intent": intent,
                "status": status, "reason": reason, "provider": self.planner.name,
                "context_revision": snapshot["revision"], "created_at": self.store.clock(),
                "expires_at": self.store.clock() + snapshot["profile"]["proposal_ttl_s"],
                "evidence": snapshot["facts"], "profile": snapshot["profile"], "mode": snapshot["mode"]}
        with self.store.transaction():
            self.store.save_plan(scope, plan)
            self.store.event(scope, "proposed", plan)
        return plan

    def execute_simulation(self, scope, plan_id):
        with self.store.transaction():
            plan = self.store.load_plan(scope, plan_id)
            if plan["status"] == "executed_simulation":
                return plan  # Idempotent retry; no second battery debit.
            snapshot = self.store.snapshot(scope)
            if snapshot["mode"] != "simulation":
                raise ValueError("La ejecución está disponible sólo en simulación")
            if plan["status"] != "ready":
                raise ValueError("La propuesta no está autorizada para simularse")
            if not plan["created_at"] <= self.store.clock() <= plan["expires_at"]:
                raise ValueError("La propuesta venció. Genera una nueva")
            if snapshot["revision"] != plan["context_revision"]:
                raise ValueError("El contexto cambió. Genera una nueva propuesta")
            status, reason = assess(snapshot, plan["intent"])
            if status != "ready":
                raise ValueError(reason)
            action, target = plan["intent"]["action"], plan["intent"]["target"]
            if action in ("navigate", "inspect", "dock"):
                battery = snapshot["facts"]["battery"]["value"]
                self.store._observe(scope, {"position": target, "battery": max(0, battery - 3)},
                                    "simulator", 1.0, self.store.clock())
            result = {"simulation": True, "action": action, "target": target,
                      "message": "Tarea simulada completada. No se enviaron comandos a motores."}
            if action == "inspect":
                result["finding"] = "Ejemplo simulado: revisión registrada; no representa una medición física."
            if action == "report":
                result["context"] = snapshot
            plan.update(status="executed_simulation", result=result)
            self.store.save_plan(scope, plan)
            self.store.event(scope, "executed_simulation", result)
            return plan
