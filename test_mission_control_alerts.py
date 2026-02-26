import sys
import types

# Isolate alert tests from unrelated optional maritime capture dependencies.
api_maritime_aviation_stub = types.ModuleType("api_maritime_aviation")
api_maritime_aviation_stub.add_maritime_aviation_routes = lambda app: app
sys.modules["api_maritime_aviation"] = api_maritime_aviation_stub

from fastapi.testclient import TestClient

import api_server


client = TestClient(api_server.app)


def setup_function() -> None:
    api_server.ALERTS.clear()
    api_server.ALERT_CLIENTS.clear()


def test_distress_alert_is_promoted_to_critical() -> None:
    response = client.post(
        "/alerts",
        json={
            "title": "Urgent marine call",
            "description": "Possible emergency traffic",
            "transcript": "MAYDAY, engine fire onboard",
            "source": "kenneth-sdr",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["severity"] == "critical"
    assert payload["source"] == "kenneth-sdr"


def test_non_distress_alert_defaults_to_warning() -> None:
    response = client.post(
        "/alerts",
        json={
            "title": "Routine channel activity",
            "description": "Regular VHF chatter",
            "signal_type": "marine_vhf",
            "source": "kenneth-sdr",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["severity"] == "warning"


def test_dispatch_to_mission_control_conversation_and_kanban(monkeypatch) -> None:
    sent = []

    def fake_post_json(url, payload, headers, timeout):
        sent.append(
            {
                "url": url,
                "payload": payload,
                "headers": headers,
                "timeout": timeout,
            }
        )

    monkeypatch.setenv("MC_CONVERSATION_WEBHOOK_URL", "http://mc.local/conversation")
    monkeypatch.setenv("MC_KANBAN_WEBHOOK_URL", "http://mc.local/kanban")
    monkeypatch.setenv("MC_WEBHOOK_BEARER_TOKEN", "secret-token")
    monkeypatch.setenv("MC_WEBHOOK_TIMEOUT", "7")
    monkeypatch.setattr(api_server, "_post_json", fake_post_json)

    response = client.post(
        "/alerts",
        json={
            "title": "Signal detected",
            "description": "Test Mission Control routing",
            "source": "kenneth-sdr",
        },
    )

    assert response.status_code == 200
    assert len(sent) == 2

    first = sent[0]
    second = sent[1]

    assert first["url"] == "http://mc.local/conversation"
    assert first["payload"]["channel"] == "conversation"
    assert first["headers"]["Authorization"] == "Bearer secret-token"
    assert first["timeout"] == 7

    assert second["url"] == "http://mc.local/kanban"
    assert second["payload"]["channel"] == "kanban"
    assert second["headers"]["Authorization"] == "Bearer secret-token"
    assert second["timeout"] == 7
