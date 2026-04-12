from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from toon_format import decode as _decode

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def h2md(skill_loader):
    return skill_loader("h2md")


@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def fixture_dir():
    return FIXTURE_DIR


def _read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text()


@pytest.fixture
def read_fixture():
    return _read_fixture


@pytest.fixture
def invoke(run, h2md):
    def _invoke(*args: str, **kwargs):
        return run(h2md.app, args, **kwargs)
    return _invoke


@pytest.fixture
def decode():
    def _fn(text: str) -> dict[str, Any]:
        result = _decode(text)
        assert isinstance(result, dict)
        return result
    return _fn


@pytest.fixture
def mock_fetch(h2md):
    def _mock(html_content: str, status_code: int = 200, url: str = "https://example.com/article"):
        mock_response = MagicMock()
        mock_response.content = html_content.encode()
        mock_response.text = html_content
        mock_response.status_code = status_code
        mock_response.url = url
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get = MagicMock(return_value=mock_response)

        return patch.object(h2md.httpx, "Client", return_value=mock_client)

    return _mock
