# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Explicit outbound context export to a user-selected agent platform."""
import hashlib
import hmac
import json
import uuid
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler
from .planner import NoRedirect


def context_envelope(snapshot, event_id=None):
    # Deliberately exclude commands, user text, event history and secrets.
    return {"schema_version": "1.1", "type": "robot.context", "event_id": event_id or str(uuid.uuid4()),
            "user_id": snapshot["user_id"], "robot_id": snapshot["robot_id"],
            "at": snapshot["at"], "revision": snapshot["revision"], "mode": snapshot["mode"],
            "facts": {k: v for k, v in snapshot["facts"].items()
                      if k in ("battery", "obstacle", "estop", "position")}}


class AgentGateway:
    def __init__(self, endpoint, token, signing_secret):
        url = urlsplit(endpoint)
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.fragment:
            raise ValueError("Configura un endpoint HTTPS sin credenciales en la URL")
        if not token or not signing_secret or "\n" in token or "\r" in token:
            raise ValueError("Token y secreto requeridos")
        self.endpoint, self.token = endpoint, token
        self.signing_secret = signing_secret.encode()

    def publish(self, snapshot, event_id=None):
        body = json.dumps(context_envelope(snapshot, event_id), sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode()
        envelope = json.loads(body)
        signature = hmac.new(self.signing_secret, body, hashlib.sha256).hexdigest()
        request = Request(self.endpoint, body, {"Content-Type": "application/json",
            "Authorization": "Bearer " + self.token, "X-ROSA-Signature": "sha256=" + signature,
            "Idempotency-Key": envelope["event_id"]})
        # No redirects: do not forward credentials to an unexpected server.
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=10) as response:
            return {"status": response.status, "event_id": envelope["event_id"]}


def record_advisory(store, scope, advisory):
    """Application must authenticate sender first. Advice has no execution authority."""
    if (not isinstance(advisory, dict) or set(advisory) != {"agent_id", "message"}
            or not isinstance(advisory["agent_id"], str) or not 1 <= len(advisory["agent_id"]) <= 80
            or not isinstance(advisory["message"], str) or not 1 <= len(advisory["message"]) <= 2000):
        raise ValueError("Consejo inválido")
    store.robot(scope)
    store.event(scope, "agent_advisory", {**advisory, "authority": "advisory_only"})
