# ROSA

**Robotics Operational Systems and Agave** · An open-source project by CDT.

**Context checks for robot commands.** An experimental, MIT-licensed Python toolkit with scoped robot context, command proposals, local AI and ROS 2 adapters.

**Minerva · v0.3.1** — named after Guadalajara and its region. [Español](docs/README.es.md) · [Architecture](docs/ARCHITECTURE.md) · [Integrations](docs/INTEGRACIONES.md) · [Contributing](CONTRIBUTING.md)

[Website](https://rosa.cdtglobal.org/) · [Try the simulator](https://rosa.cdtglobal.org/demo) · [Test results](https://github.com/IgDiaz/ROSA/actions/workflows/tests.yml)

Ask a robot to **inspect line 2**. With fresh context and enough battery, the simulator can accept the task. With a blocked path, low battery or stale observations, the same request is rejected with an inspectable reason.

This is a context and command layer for robot applications, not a new operating-system kernel. ROS 2 remains responsible for its own drivers, middleware and application stack. The included runtime executes **simulated effects only**.

## Quickstart

Python 3.11 or newer. No extra dependencies or network connection are needed for the offline demo.

```bash
git clone https://github.com/IgDiaz/ROSA.git
cd ROSA
python -m rosa
```

Open **http://127.0.0.1:8765**. On Windows you can also open `iniciar-demo.bat`; on macOS/Linux use `python3` if necessary. Use `--port 8770` if needed. `Ctrl+C` stops the server.

1. Propose **Inspect line 2** and confirm the simulation.
2. Select **Low battery** and propose the same task.
3. Try **Return to base**.
4. Select **No telemetry**, wait more than three seconds, and propose movement.

The diagram animates discrete state changes; it is not a physics or navigation simulator. Inspections generate labelled example findings, not sensor measurements.

## Libraries and codenames

| Name | Module | Responsibility |
|---|---|---|
| **Colomos** | `rosa.context` | User/robot scope, observation provenance, freshness, revision and SQLite memory |
| **Minerva** | `rosa.policy`, `rosa.runtime` | Allowed intents, deterministic checks, expiring proposals and idempotent simulation |
| **Tequila** | `rosa.planner` | Small offline grammar or an optional local Ollama interpreter |
| **Tonalá** | `rosa.ros2` | Optional ROS 2 telemetry observer and context publisher |
| **Chapala** | `rosa.gateway` | Explicit signed HTTPS context export and advisory recording |

These are names within one Python package, not five separately published packages. No PyPI publication or ROS distribution release is claimed.

## Use the SDK

Run from the repository, or install with `python -m pip install .`:

```python
from rosa import ContextStore, Runtime, Scope

store = ContextStore(":memory:")
robot = Scope("factory", "amr_01")
store.register(robot, mode="simulation")
store.observe(robot, {
    "battery": 82, "obstacle": False,
    "estop": False, "position": "base",
}, source="simulator")

runtime = Runtime(store)
plan = runtime.propose(robot, "Inspect line 2")
print(plan["status"], plan["reason"])

# In your application, obtain operator confirmation before calling this.
if plan["status"] == "ready":
    print(runtime.execute_simulation(robot, plan["id"])["result"])
store.close()
```

Every observation has a source, timestamp and confidence value. Confidence is supplied by the adapter, not a calibrated safety probability. Battery/position expire after 10 seconds; obstacle/stop after 3. Proposals expire after 30 seconds and are checked again before simulation. A semantic context change invalidates an older proposal. Repeating a confirmed proposal cannot duplicate its effect, even after reopening SQLite.

The demo uses four fixed facts and five actions. Thresholds are demonstration settings, not robot-specific limits. There is no trained context model, sensor fusion, causal reasoning, fault prediction or continuous learning.

## Optional adapters

With Ollama running locally and a model already installed:

```bash
python -m rosa --ollama-model YOUR_INSTALLED_MODEL
```

Select Ollama in the local console. The model receives current context and up to five recent events from the same scope. Its output must pass schema and policy checks; it cannot write sensor facts, modify rules or execute arbitrary code. Model licenses and hardware needs are separate. Operator confirmation remains necessary because a model can misunderstand an otherwise valid request.

Tonalá observes ROS 2 battery, obstacle, stop and registered-position topics, then publishes JSON context. Observation profiles cannot execute. No actuator publisher is included.

Chapala exports a minimal context event to a configured HTTPS endpoint with a bearer token, HMAC signature and event ID. No data is transmitted automatically. The receiver must authenticate, enforce scope and deduplicate events. See [integration contracts](docs/INTEGRACIONES.md).

ROS 2, a real Ollama model and an external receiver have **not been validated end to end in this release**. Adapter contracts use controlled tests. This software is not a functional-safety system or a physical emergency stop.

## Repository scope

This public repository contains the robotics SDK, optional adapters, schemas,
examples, local simulation console and tests. The console in `rosa/web/` is a
functional SDK tool served on loopback; it is not the project's landing page.

The public website is maintained separately and consumes this SDK as a pinned
package dependency. Its application server, marketing page, hosting configuration
and deployment history are not part of this repository. Installing ROSA does not
require the website or a hosted account.

See [privacy and data handling](PRIVACY.md) and the [security policy](SECURITY.md).

## Repository layout

| Directory | Contents |
|---|---|
| `rosa/` | Core, optional adapters and local console entry points |
| `rosa/web/` | Local simulation console and its icon |
| `examples/` | Runnable SDK examples |
| `schemas/` | JSON contracts |
| `tests/` | Core, adapter and public-session tests |
| `docs/` | Architecture, Spanish guide, integrations, validation and roadmap |
| `.github/` | CI and issue/PR templates |

## Tests

```bash
# SDK, adapter contracts and loopback console: standard library only
python -m unittest discover -s tests -v
```

See [validation notes](docs/VALIDACION.md) for completed checks. Contributions should include reproducible scenarios and narrowly scoped changes; performance claims need measurements.

## License and provenance

Original code: copyright © 2026 CDT, released under the [MIT License](LICENSE). The original MIT text remains unchanged. [LICENSE-CDT](LICENSE-CDT) separately records CDT's grant for its original contributions under the same MIT terms; it adds no restrictions and does not replace any upstream license or notice.

ROS and ROS 2 are ecosystems with component-specific licenses, not a single MIT-licensed dependency. Third-party libraries, ROS packages and model weights retain their own licenses and notices; see [third-party notices](THIRD_PARTY_NOTICES.md). No affiliation with or endorsement by ROS, Open Robotics or Ollama is implied.

This initial implementation was developed with AI assistance. Maintainer review, independent tests and hardware validation remain necessary before expanding its scope.

Primary references: [ROS 2](https://github.com/ros2), [ROS 2 actions](https://design.ros2.org/articles/actions.html), [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs), [Ollama chat API](https://docs.ollama.com/api/chat). The ROS homepage blocked automated retrieval; official documentation informed the adapters. Architecture and demo thresholds are this project's choices.
