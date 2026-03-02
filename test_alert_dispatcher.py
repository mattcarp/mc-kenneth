import alert_dispatcher


def test_send_stress_alert_uses_env_credentials(monkeypatch) -> None:
    captured = {}

    def fake_post(bot_token, chat_id, text, timeout):
        captured["bot_token"] = bot_token
        captured["chat_id"] = chat_id
        captured["text"] = text
        captured["timeout"] = timeout

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-42")
    monkeypatch.setenv("TELEGRAM_ALERT_TIMEOUT", "9")
    monkeypatch.setattr(alert_dispatcher, "_post_telegram_message", fake_post)

    success = alert_dispatcher.send_stress_alert(
        stress_score=88,
        frequency=156800000,
        transcription="Caller panicking near harbor entrance.",
        indicators={"speech_rate": "high", "voiced_ratio": 0.74},
    )

    assert success is True
    assert captured["bot_token"] == "env-token"
    assert captured["chat_id"] == "chat-42"
    assert captured["timeout"] == 9
    assert "Stress score: 88.0%" in captured["text"]
    assert "Frequency: 156.800 MHz" in captured["text"]
    assert "Transcription preview: Caller panicking near harbor entrance." in captured["text"]


def test_send_stress_alert_uses_token_file_fallback(monkeypatch) -> None:
    captured = {}

    def fake_post(bot_token, chat_id, text, timeout):
        captured["bot_token"] = bot_token
        captured["chat_id"] = chat_id
        captured["text"] = text
        captured["timeout"] = timeout

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setattr(alert_dispatcher, "_read_bot_token_from_file", lambda: "file-token")
    monkeypatch.setattr(alert_dispatcher, "_post_telegram_message", fake_post)

    success = alert_dispatcher.send_stress_alert(
        stress_score=0.91,
        frequency=None,
        transcription="",
        indicators=["panic", "fast speech"],
    )

    assert success is True
    assert captured["bot_token"] == "file-token"
    assert captured["chat_id"] == alert_dispatcher.DEFAULT_CHAT_ID
    assert "Stress score: 91.0%" in captured["text"]
    assert "Frequency: unknown" in captured["text"]
    assert "Transcription preview: N/A" in captured["text"]


def test_send_stress_alert_returns_false_without_token(monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setattr(alert_dispatcher, "_read_bot_token_from_file", lambda: None)

    success = alert_dispatcher.send_stress_alert(
        stress_score=75,
        frequency=121500000,
        transcription="Mayday call",
        indicators={"term": "mayday"},
    )

    assert success is False
