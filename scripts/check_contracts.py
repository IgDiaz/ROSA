"""Verify that real SDK outputs match the published JSON contracts."""
import json
from pathlib import Path
import jsonschema
from rosa import ContextStore, Scope, Runtime
from rosa.gateway import context_envelope

root = Path(__file__).resolve().parents[1]
store = ContextStore()
scope = Scope("contracts", "amr")
store.register(scope)
try:
    store.observe(scope, {"battery": 82, "obstacle": False, "estop": False, "position": "base"}, "simulator")
    plan = Runtime(store).propose(scope, "inspect line 2")
    for filename, payload in (("intent.schema.json", plan["intent"]),
                              ("context-event.schema.json", context_envelope(store.snapshot(scope)))):
        schema = json.loads((root / "schemas" / filename).read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(payload, schema)
        print(filename + ": actual SDK output conforms")
    schema = json.loads((root / "schemas/telemetry.schema.json").read_text())
    jsonschema.validate({"schema_version": "1.0", "user_id": "contracts", "robot_id": "amr",
                         "observed_at": store.clock(), "sequence": 1,
                         "values": {"battery": 82}}, schema)
    print("telemetry.schema.json: valid acquisition packet conforms")
finally:
    store.close()
