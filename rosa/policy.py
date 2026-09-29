# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Deterministic application gates; not a certified robot safety system."""
from .context import CAPABILITIES, DESTINATIONS, TTL
from .profile import OperationalProfile

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
    profile = OperationalProfile.from_dict(snapshot.get("profile", {}))
    action = intent["action"]
    if action == "clarify":
        return "clarify", "Necesito una tarea y un destino concretos, por ejemplo: inspecciona línea 2."
    if action not in snapshot["capabilities"]:
        return "blocked", "Este robot no tiene registrada esa capacidad."
    if action in ("hold", "report"):
        return "ready", "La tarea no requiere desplazamiento. Los datos vencidos se muestran como tales."
    for name in TTL:
        fact = snapshot["facts"].get(name)
        if not fact or not fact["fresh"] or fact["confidence"] < profile.minimum_confidence:
            return "blocked", f"No hay evidencia reciente y confiable de {name}. Actualiza la telemetría."
        if profile.allowed_sources and fact["source"] not in profile.allowed_sources:
            return "blocked", f"La fuente de {name} no pertenece al perfil operativo."
        if profile.require_acquisition_time and fact.get("timestamp_kind") != "acquired":
            return "blocked", f"Falta fecha de adquisición verificable de {name}."
    f = {key: item["value"] for key, item in snapshot["facts"].items()}
    if f["estop"]:
        return "blocked", "El paro está activo. Resuelve la condición antes de proponer movimiento."
    if f["obstacle"]:
        return "blocked", "Hay un obstáculo reportado. Espera a que la ruta esté libre."
    minimum = profile.docking_battery if action == "dock" else profile.minimum_battery
    if f["battery"] < minimum:
        reason = "Carga insuficiente para desplazarse incluso a la base." if action == "dock" else f"Batería por debajo del {minimum:g} %. Propón volver a la base."
        return "blocked", reason
    return "ready", "Contexto reciente, capacidad registrada, ruta libre y batería suficiente."
