"""Tests for hosted free-tier privacy and webhook behavior."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from PIL import Image
from io import BytesIO


def _image_upload():
    img = Image.new('RGB', (100, 100), color='white')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def test_mcp_requires_token(monkeypatch):
    from webapp import app

    monkeypatch.setenv("MCP_TOKEN", "secret")
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.post('/mcp', json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response.status_code == 401


def test_mcp_accepts_correct_token(monkeypatch):
    from webapp import app

    monkeypatch.setenv("MCP_TOKEN", "secret")
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.post(
            '/mcp',
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={"Authorization": "Bearer secret"},
        )
        assert response.status_code == 200
        assert "tools" in response.get_json()["result"]


@patch('webapp.detect_text_local')
def test_rate_failure_does_not_return_raw_ocr(mock_ocr, caplog):
    from webapp import app

    mock_ocr.return_value = ["Nickname", "Unreadable Text"]
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.post(
            '/rate',
            data={'image': (_image_upload(), 'test.png')},
            content_type='multipart/form-data',
        )
    assert response.status_code == 422
    body = response.get_json()
    assert "ocr_raw" not in body
    assert "Nickname" not in json.dumps(body)
    assert "Nickname" not in caplog.text


@patch('webapp.build_application')
def test_telegram_webhook_requires_secret(mock_build, monkeypatch):
    from webapp import app

    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "expected")
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.post('/telegram/webhook/wrong', json={"update_id": 1})
    assert response.status_code == 404
    mock_build.assert_not_called()


@patch('webapp.Update')
@patch('webapp.build_application')
def test_telegram_webhook_processes_update(mock_build, mock_update, monkeypatch):
    from webapp import app

    tg_app = MagicMock()
    tg_app.bot = MagicMock()
    tg_app.initialize = AsyncMock()
    tg_app.process_update = AsyncMock()
    tg_app.shutdown = AsyncMock()
    mock_build.return_value = tg_app
    mock_update.de_json.return_value = MagicMock()

    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "expected")
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.post('/telegram/webhook/expected', json={"update_id": 1})

    assert response.status_code == 200
    tg_app.initialize.assert_awaited_once()
    tg_app.process_update.assert_awaited_once()
    tg_app.shutdown.assert_awaited_once()
