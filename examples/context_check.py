"""Same request, different context. Run: python -m examples.context_check."""
from rosa import ContextStore, Runtime, Scope


def main():
    store = ContextStore()
    robot = Scope("example", "minerva_01")
    store.register(robot)
    runtime = Runtime(store)
    for battery in (82, 14):
        # Synthetic trusted observations, never physical telemetry.
        store.observe(robot, {"battery": battery, "position": "base",
                              "obstacle": False, "estop": False}, "simulator")
        plan = runtime.propose(robot, "Inspect line 2")
        print(f"Battery {battery}%: {plan['status']} — {plan['reason']}")
    store.close()


if __name__ == "__main__":
    main()
