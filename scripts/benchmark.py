"""Reproducible local timing evidence; not a comparison with ROS 2 or a robot."""
import json
import platform
import statistics
import time
from rosa import ContextStore, Runtime, Scope, __version__


def main():
    samples = []
    store = ContextStore()
    scope = Scope("benchmark", "amr")
    store.register(scope)
    runtime = Runtime(store)
    try:
        for _ in range(500):
            store.observe(scope, {"battery": 82, "obstacle": False, "estop": False,
                                  "position": "base"}, "simulator")
            start = time.perf_counter_ns()
            plan = runtime.propose(scope, "inspect line 2")
            runtime.execute_simulation(scope, plan["id"])
            samples.append((time.perf_counter_ns() - start) / 1_000_000)
    finally:
        store.close()
    print(json.dumps({"version": __version__, "python": platform.python_version(),
                      "platform": platform.platform(), "iterations": len(samples),
                      "scenario": "in-memory SQLite, rules interpreter, proposal + simulation",
                      "p50_ms": round(statistics.median(samples), 4),
                      "p95_ms": round(sorted(samples)[474], 4)}, indent=2))


if __name__ == "__main__":
    main()
