# Public API · ROSA 0.4

Import the following from `rosa`. Invalid input raises `ValueError`; transport and database failures may propagate their native exceptions. Integrators decide retry and operator-notification behavior.

| API | Purpose / return |
|---|---|
| `Scope(user_id, robot_id)` | Immutable scope; 1–64 letters, numbers, hyphens or underscores per identifier |
| `OperationalProfile(...)` | Immutable operating requirements; `to_dict()` / `from_dict()` provide JSON configuration |
| `ContextStore(path=":memory:", clock=time.time)` | SQLite storage; call `close()` when finished |
| `register(scope, mode="simulation", capabilities=..., profile=None)` | Create a robot once; an existing robot is retained. Use `configure()` for explicit requirement changes |
| `profile(scope)` | Return stored `OperationalProfile` |
| `configure(scope, profile)` | Change requirements, increment context revision and record an event |
| `observe(scope, values, source, confidence=1, observed_at=None, sequence=None)` | Ingest validated facts atomically; ignore old timestamps/replayed sequence numbers |
| `snapshot(scope)` | Version 1.1 context with requirements, facts, provenance, acquisition/reception times and current freshness |
| `history(scope, limit=30)` | Most recent scoped events first; limit capped at 200 |
| `Runtime(store, planner=None)` | Use the offline grammar or an object implementing `name` and `propose(text, snapshot)` |
| `Runtime.propose(scope, text)` | Persist proposal: `ready`, `blocked` or `clarify`, with reason and evidence |
| `Runtime.execute_simulation(scope, plan_id)` | Recheck and apply a simulation once; repeated confirmations return the saved result |
| `ingest_telemetry(store, scope, payload, source="ros2/telemetry")` | Validate and ingest an acquisition-time JSON packet from an authenticated transport |

`OperationalProfile` fields: `battery_ttl_s`, `obstacle_ttl_s`, `estop_ttl_s`, `position_ttl_s`, `minimum_battery`, `docking_battery`, `minimum_confidence`, `proposal_ttl_s`, `require_acquisition_time`, `allowed_sources`. TTLs must be positive and at most 86400 seconds; battery thresholds are percentages. Defaults reproduce the local demo. Values must be selected and validated for the target system.

## Optional adapters

`rosa.planner.OllamaPlanner(model, endpoint="http://127.0.0.1:11434", timeout=35)` accepts literal loopback endpoints only. `propose()` returns a validated intent.

`rosa.gateway.AgentGateway(endpoint, token, signing_secret).publish(snapshot, event_id=None)` performs one HTTPS request. Preserve `event_id` across retries. `context_envelope(snapshot)` creates the export; `record_advisory(store, scope, advisory)` stores an authenticated agent's text without changing sensor evidence or executing tasks.

`rosa.ros2` is a CLI observer. See integration contracts for topics, input timestamps, QoS and source authentication. `_observe`, database tables and HTTP demo routes are internal integration details rather than a stable multiuser service API.

## Guarantees and responsibilities

A policy/profile change invalidates older unexecuted proposals. An observation heartbeat can refresh time without changing semantic revision. Sequence numbers are tracked per fact and source and survive restarts. They must keep increasing; use a deliberately provisioned new source identity if a sensor sequence legitimately resets. Source allowlists do not authenticate arbitrary Python callers or ROS publishers.

An old completed proposal remains an idempotent historical result after configuration changes. Recording a result again does not reapply its simulation effect. The API never translates these methods into actuator commands.
