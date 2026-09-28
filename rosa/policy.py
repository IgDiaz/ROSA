# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Deterministic application gates; not a certified robot safety system."""
from .context import CAPABILITIES, DESTINATIONS, TTL

INTENT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["action", "target"],
    "properties": {"action": {"type": "string", "enum": [*CAPABILITIES, "clarify"]},
                   "target": {"type": ["string", "null"], "enum": [*DESTINATIONS, None]}}}


def validate_intent(value):
    if not isinstance(value, dict) or set(value) != {"action", "target"}:
        raise ValueError("La intención debe contener únicamente action y target")
    action, target = value["action"], value["target"]
    if action not in (*CAPABILITIES, "clarify") or target not in (*DESTINATIONS, None):
        raise ValueError("Acción o destino no permitido")
    if action in ("navigate", "inspect") and target is None:
        raise ValueError("Falta un destino")
    if action == "dock" and target != "base":
        raise ValueError("La recarga requiere base")
    if action in ("hold", "report", "clarify") and target is not None:
        raise ValueError("Esta acción no acepta destino")
    return dict(value)


def assess(snapshot, intent):
    intent = validate_intent(intent)
    action = intent["action"]
    if action == "clarify":
        return "clarify", "Necesito una tarea y un destino concretos, por ejemplo: inspecciona línea 2."
    if action not in snapshot["capabilities"]:
        return "blocked", "Este robot no tiene registrada esa capacidad."
    if action in ("hold", "report"):
        return "ready", "La tarea no requiere desplazamiento. Los datos vencidos se muestran como tales."
    for name in TTL:
        fact = snapshot["facts"].get(name)
        if not fact or not fact["fresh"] or fact["confidence"] < 0.8:
            return "blocked", f"No hay evidencia reciente y confiable de {name}. Actualiza la telemetría."
    f = {key: item["value"] for key, item in snapshot["facts"].items()}
    if f["estop"]:
        return "blocked", "El paro está activo. Resuelve la condición antes de proponer movimiento."
    if f["obstacle"]:
        return "blocked", "Hay un obstáculo reportado. Espera a que la ruta esté libre."
    minimum = 8 if action == "dock" else 20
    if f["battery"] < minimum:
        reason = "Carga insuficiente para desplazarse incluso a la base." if action == "dock" else "Batería por debajo del 20 %. Propón volver a la base."
        return "blocked", reason
    return "ready", "Contexto reciente, capacidad registrada, ruta libre y batería suficiente."
