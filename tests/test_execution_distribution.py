"""Distribution settings remain separate through the real desktop constructor."""

from pathlib import Path

import pytest
from bioimage_app.web_window import WebWorkbenchWindow
from PySide6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from tooling.qt_test_lifecycle import close_and_dispose_window


@pytest.mark.parametrize(
    ("channel", "namespace"),
    [
        ("candidate", "Candidate"),
        ("win10-test", "Win10Test"),
        ("wb-execution-test", "E7Test"),
        ("wb-grouped-intake-test", "GroupedIntakeTest"),
        ("wb-fig-sequence-test", "FigSequenceTest"),
        ("wb-automatic-flow-test", "AutomaticFlowTest"),
        ("wb-reliable-crop-test", "ReliableCropTest"),
        ("unknown", "Platform"),
    ],
)
def test_distribution_constructor_never_reuses_another_settings_namespace(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    channel: str,
    namespace: str,
) -> None:
    calls: list[tuple[str, str]] = []

    def isolated_settings(organization: str, application: str) -> QSettings:
        calls.append((organization, application))
        # Observe the production constructor selection without reading/writing
        # any real user registry/settings namespace during the regression.
        return QSettings(str(tmp_path / (application + ".ini")), QSettings.Format.IniFormat)

    monkeypatch.setenv("BIOIMAGE_RELEASE_CHANNEL", channel)
    monkeypatch.setattr("bioimage_app.web_window.QSettings", isolated_settings)
    window = WebWorkbenchWindow()
    window.show()
    try:
        assert calls == [("BioImageTools", namespace)]
        window.settings.setValue("owned-regression", namespace)
        window.settings.sync()
        assert list(tmp_path.glob("*.ini")) == [tmp_path / (namespace + ".ini")]
        assert window.settings.value("owned-regression") == namespace
    finally:
        close_and_dispose_window(
            window, qtbot, resources_closed=lambda: window.host.resources_closed, timeout=20000
        )
