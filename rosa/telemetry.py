# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Acquisition-time telemetry contract shared by transport adapters."""
import json


def ingest_telemetry(store, scope, payload, *, source="ros2/telemetry"):
    """Accept one bounded JSON observation packet for an already selected scope.

    The transport must authenticate the publisher. Payloads cannot choose their
    trusted source name. Acquisition time is Unix seconds on synchronized clocks;
    sequence numbers must increase across restarts of a given source.
    """
    if not isinstance(payload, str) or len(payload.encode("utf-8")) > 8192:
        raise ValueError("Telemetría JSON limitada a 8192 bytes")
    data = json.loads(payload)
    required = {"schema_version", "user_id", "robot_id", "observed_at", "sequence", "values"}
    if not isinstance(data, dict) or set(data) != required or data["schema_version"] != "1.0":
        raise ValueError("Contrato de telemetría inválido")
    if (data["user_id"], data["robot_id"]) != scope.key:
        raise ValueError("La telemetría pertenece a otro robot")
    if data["observed_at"] is None or data["sequence"] is None:
        raise ValueError("Adquisición y secuencia requeridas")
    store.observe(scope, data["values"], source=source,
                  observed_at=data["observed_at"], sequence=data["sequence"])
