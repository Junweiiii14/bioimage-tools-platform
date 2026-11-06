"""Optional WB window owned by the web shell."""

from PySide6.QtGui import QCloseEvent

from bioimage_app.figure_window import FigureProjectWindow


class AdvancedHost(FigureProjectWindow):
    shutdown_requested = False

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self.shutdown_requested:
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)
