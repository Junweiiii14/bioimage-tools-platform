"""Approved T-028 native workbench palette and component styling."""

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QWidget


def apply_workbench_theme(window: QWidget) -> None:
    window.setFont(QFont("Microsoft YaHei UI", 10))
    palette = QPalette(window.palette())
    for role, value in (
        (QPalette.ColorRole.Window, "#f6f5f2"),
        (QPalette.ColorRole.WindowText, "#202523"),
        (QPalette.ColorRole.Base, "#ffffff"),
        (QPalette.ColorRole.AlternateBase, "#f5f5f2"),
        (QPalette.ColorRole.Text, "#202523"),
        (QPalette.ColorRole.Button, "#ffffff"),
        (QPalette.ColorRole.ButtonText, "#202523"),
        (QPalette.ColorRole.Highlight, "#256f82"),
        (QPalette.ColorRole.HighlightedText, "#ffffff"),
        (QPalette.ColorRole.ToolTipBase, "#ffffff"),
        (QPalette.ColorRole.ToolTipText, "#202523"),
    ):
        palette.setColor(role, QColor(value))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#6b726d"))
    window.setPalette(palette)
    window.setStyleSheet("""
        QMainWindow { background: #f6f5f2; color: #202523; }
        QLabel, QCheckBox, QRadioButton { color: #202523; background: transparent; }
        QLabel:disabled, QCheckBox:disabled, QRadioButton:disabled { color: #6b726d; }
        QToolBar { background: #ffffff; border: 0; border-bottom: 1px solid #e4e5e0;
            padding: 8px 14px; spacing: 8px; }
        QLabel#appBrand { font-size: 16px; font-weight: 600; padding-right: 8px; }
        QLabel#saveState { color: #636b65; padding: 2px 8px; }
        QPushButton, QToolButton { color: #202523; background: #ffffff;
            border: 1px solid #d9dcd5; border-radius: 6px; padding: 6px 10px; }
        QPushButton:hover, QToolButton:hover { background: #edf3f3; border-color: #8badb3; }
        QPushButton:pressed, QToolButton:pressed { background: #dce9eb; }
        QPushButton:focus, QToolButton:focus { border: 2px solid #256f82; }
        QPushButton:disabled, QToolButton:disabled { color: #6b726d; background: #eeefeb;
            border-color: #e2e4dd; }
        QPushButton#primaryAction { background: #256f82; color: #ffffff; border-color: #256f82; }
        QPushButton#primaryAction:hover { background: #205e6e; }
        QPushButton#primaryAction:disabled { background: #eeefeb; color: #6b726d;
            border-color: #e2e4dd; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
            color: #202523; background: #ffffff; border: 1px solid #d9dcd5;
            border-radius: 4px; padding: 5px; selection-background-color: #256f82; }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border-color: #256f82; }
        QComboBox QAbstractItemView { background: #ffffff; color: #202523;
            selection-background-color: #256f82; selection-color: #ffffff; }
        QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
            background: #ffffff; border: 0; }
        QSplitter::handle { background: #e5e6e0; }
        QTableWidget { background: #ffffff; color: #202523; gridline-color: #eaebe6;
            selection-background-color: #e3eef0; selection-color: #174f60; border: 0; }
        QHeaderView::section { background: #f3f4f0; color: #505953; border: 0;
            border-bottom: 1px solid #e0e3dc; padding: 7px; }
        QTableCornerButton::section { background: #f3f4f0; border: 0; }
        QTabWidget::pane { border: 0; background: #ffffff; }
        QTabBar::tab { color: #505953; background: transparent; padding: 7px 12px; }
        QTabBar::tab:selected { color: #256f82; background: #eaf1f2; }
        QWidget#workflowNavigation, QListWidget#workflowSteps { background: #ffffff; border: 0; }
        QListWidget#workflowSteps::item { color: #626b65; padding: 9px 24px; }
        QListWidget#workflowSteps::item:selected { color: #205e6e; background: #edf3f3; }
        QListWidget#workflowSteps::item:hover { background: #f4f6f2; }
        QListWidget#evidenceSources { background: #ffffff; border: 0; }
        QListWidget#evidenceSources::item { padding: 8px; color: #202523; }
        QListWidget#evidenceSources::item:selected { background: #e3eef0; color: #174f60; }
        QListWidget#evidenceSources::item:hover { background: #f1f4ef; }
        QWidget#evidenceWorkbench, QWidget#evidenceStage { background: #f6f5f2; }
        QWidget#evidenceControls, QWidget#evidenceReview { background: #ffffff; }
        QLabel#evidenceHeading, QLabel#exportHeading { font-size: 15px; font-weight: 600; }
        QLabel#evidenceSummary, QLabel#stepHelp, QLabel#projectCaption { color: #626b65; }
        QLabel#stepTitle { font-size: 18px; font-weight: 600; }
        QLineEdit#projectName { background: transparent; border: 0; font-size: 17px;
            font-weight: 600; padding: 2px 4px; }
        QLineEdit#projectName:focus { background: #ffffff; border: 1px solid #256f82; }
        QLabel#welcomeTitle { font-size: 24px; font-weight: 600; }
        QLabel#welcomeWorkflow { color: #626b65; padding: 12px 0; }
        QMenu { color: #202523; background: #ffffff; border: 1px solid #d9dcd5; }
        QMenu::item { padding: 8px 20px; }
        QMenu::item:selected { color: #ffffff; background: #256f82; }
        QProgressBar#taskProgress { border: 0; background: #edf0e9; max-height: 3px; }
        QProgressBar#taskProgress::chunk { background: #256f82; }
        QScrollBar:vertical { width: 10px; background: #f6f5f2; margin: 0; }
        QScrollBar::handle:vertical { background: #b7c1b9; min-height: 24px; border-radius: 4px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """)
