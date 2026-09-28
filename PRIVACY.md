# Privacy and data handling — ROSA SDK

Updated: 2026-09-28. Maintainer: CDT.

This notice describes the software in this repository. The separately hosted
website has its own notice at <https://rosa.cdtglobal.org/privacy>.

## Local operation

The default SDK and rule-based simulator do not send telemetry, analytics,
commands or robot data to CDT. No account is required. The local console binds
to `127.0.0.1` and uses an in-memory request token, not an analytics cookie.

`ContextStore` can use in-memory SQLite or a file chosen by the integrator. The
CLI defaults to `rosa-demo.sqlite3`. Stored data can include user/robot IDs,
capabilities, observations and their sources/timestamps/confidence, operator
requests, proposals, simulated results, event history and agent advisories.
The supplied IDs are application identifiers, not authenticated user accounts.

File-backed history persists until the operator removes it. There is no automatic
retention limit or database encryption in the SDK. To remove a local demo's
history, stop all processes using it and remove the selected SQLite database and
any associated journal/WAL files. Backups and previously exported copies must be
managed separately by their owner.

## Optional transfers

- **Local AI:** enabling the Ollama adapter sends the request, current context and
  up to five recent events for the same scope to a loopback Ollama endpoint.
  The SDK permits no remote endpoint for this adapter. The operator controls the
  installed service, its logs and the model's own behavior and license.
- **ROS 2:** enabling the observer reads configured topics and publishes context
  to the configured ROS graph. Other participants' access depends on the
  operator's ROS configuration; a namespace alone is not access control.
- **Agent gateway:** explicitly calling `AgentGateway.publish` sends the documented
  context envelope to the HTTPS endpoint configured by the operator. It includes
  scope identifiers, event metadata and allowlisted observations, not arbitrary
  command text, event history or secrets. A bearer credential is sent to that
  receiver for authentication, and the body is HMAC-signed. The receiver controls
  retention and onward processing. No endpoint is connected by default.
- **Exports and links:** downloading context creates a local file. Opening a link
  to the repository or website contacts that external service under its policies.

Package installation or downloading models may contact their respective
registries/providers; this is distinct from offline SDK operation.

## Your integrations and contributions

Use synthetic data in examples, issues and pull requests. Never include API
credentials, identifying employee information or confidential production data.
Integrators decide which real data to process, who may access it, where it is
stored and how long it is retained. This notice is not a substitute for the
integrator's privacy notice or access-control design.

For a privacy question, open an issue with a non-sensitive description and
request a private channel if needed. For vulnerabilities, follow [SECURITY.md](SECURITY.md).

## Resumen en español

El SDK y el simulador por reglas funcionan localmente y no envían telemetría a
CDT. El historial SQLite puede persistir en tu equipo hasta que lo elimines. Los
adaptadores opcionales sólo transmiten datos cuando los configuras y utilizas:
Ollama local, la red ROS 2 o el receptor HTTPS que elijas. Consulta las secciones
anteriores para conocer los datos y el alcance de cada transferencia. No incluyas
información confidencial ni credenciales en contribuciones públicas.
