"""Keep GUI regression windows off the user's desktop, including direct pytest runs."""

import logging
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def capture_storage_request_diagnostics(caplog: pytest.LogCaptureFixture) -> None:
    """Keep request timings in failed-test capture without exposing storage payloads."""
    caplog.set_level(logging.DEBUG, logger="bioimage_app.storage")
