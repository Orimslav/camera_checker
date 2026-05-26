import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QThread, Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dahuawin.services.camera_checker import CameraChecker
from dahuawin.services.csv_loader import CSVLoader
from dahuawin.services.demo_checker import DemoCameraChecker
from dahuawin.services.result_exporter import ResultExporter
from dahuawin.settings_dialog import SettingsDialog
from dahuawin.translations import TRANSLATIONS


LIGHT_STYLESHEET = """
QMainWindow, QWidget {
    background: #f4f7fb;
    color: #14213d;
    font-size: 14px;
}
QLabel {
    color: #14213d;
}
QPushButton {
    background: #1f6feb;
    color: white;
    border: 0;
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 700;
    min-height: 22px;
}
QPushButton:hover {
    background: #195ec8;
}
QPushButton:disabled {
    background: #c8d2de;
    color: #5c6773;
}
QPushButton[variant="language"] {
    background: white;
    border: 1px solid #b8c4d1;
    border-radius: 6px;
    padding: 4px;
}
QPushButton[variant="language"]:hover {
    background: #eef4ff;
    border: 1px solid #7aa2e3;
}
QPushButton[variant="language"][active="true"] {
    background: #dbeafe;
    border: 2px solid #1f6feb;
}
QPushButton[variant="language"]:disabled {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
}
QProgressBar {
    border: 1px solid #a9b7c8;
    border-radius: 6px;
    background: #e8eef6;
    color: #14213d;
    min-height: 24px;
    text-align: center;
    font-weight: 700;
}
QProgressBar::chunk {
    background: #2fb344;
    border-radius: 5px;
}
QGroupBox {
    border: 1px solid #b8c4d1;
    border-radius: 8px;
    margin-top: 12px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #14213d;
}
QTableWidget {
    background: white;
    alternate-background-color: #f8fafc;
    color: #111827;
    gridline-color: #d7dee8;
    border: 1px solid #b8c4d1;
    border-radius: 8px;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}
QHeaderView::section {
    background: #26364a;
    color: white;
    padding: 8px;
    border: 0;
    border-right: 1px solid #3c4b5e;
    font-weight: 700;
}
QTextEdit {
    background: white;
    color: #111827;
    border: 1px solid #b8c4d1;
    border-radius: 8px;
    padding: 10px;
}
"""


DARK_STYLESHEET = """
QMainWindow, QWidget {
    background: #0f172a;
    color: #e2e8f0;
    font-size: 14px;
}
QLabel {
    color: #e2e8f0;
}
QPushButton {
    background: #2563eb;
    color: white;
    border: 0;
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 700;
    min-height: 22px;
}
QPushButton:hover {
    background: #1d4ed8;
}
QPushButton:disabled {
    background: #334155;
    color: #94a3b8;
}
QPushButton[variant="language"] {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px;
}
QPushButton[variant="language"]:hover {
    background: #1e293b;
    border: 1px solid #60a5fa;
}
QPushButton[variant="language"][active="true"] {
    background: #172554;
    border: 2px solid #60a5fa;
}
QPushButton[variant="language"]:disabled {
    background: #0f172a;
    border: 1px solid #334155;
}
QProgressBar {
    border: 1px solid #334155;
    border-radius: 6px;
    background: #1e293b;
    color: #e2e8f0;
    min-height: 24px;
    text-align: center;
    font-weight: 700;
}
QProgressBar::chunk {
    background: #22c55e;
    border-radius: 5px;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 12px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #e2e8f0;
}
QTableWidget {
    background: #111827;
    alternate-background-color: #172033;
    color: #e5e7eb;
    gridline-color: #334155;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: #1d4ed8;
    selection-color: white;
}
QHeaderView::section {
    background: #020617;
    color: white;
    padding: 8px;
    border: 0;
    border-right: 1px solid #1e293b;
    font-weight: 700;
}
QTextEdit {
    background: #111827;
    color: #e5e7eb;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px;
}
"""


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SortableTableWidgetItem(QTableWidgetItem):
    def __init__(self, text: str, sort_value=None):
        super().__init__(text)
        self.sort_value = text if sort_value is None else sort_value

    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


class CheckWorker(QThread):
    progress_changed = Signal(int, int, dict)
    finished_with_results = Signal(list, dict)
    failed = Signal(str)

    def __init__(self, csv_path: str, demo_mode: bool = False):
        super().__init__()
        self.csv_path = csv_path
        self.demo_mode = demo_mode

    def run(self):
        try:
            checker = DemoCameraChecker() if self.demo_mode else CameraChecker(self.csv_path)
            results = checker.run_check(progress_callback=self.progress_changed.emit)
            summary = checker.summarize(results)
            self.finished_with_results.emit(results, summary)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, demo_mode: bool = False):
        super().__init__()
        self.demo_mode = demo_mode
        self.assets_dir = Path(__file__).resolve().parent.parent / "img"
        self.csv_path = "" if not demo_mode else "<demo>"
        self.results = []
        self.displayed_results = []
        self.summary = {}
        self.worker = None
        self.dark_mode = True
        self.language = "en" if demo_mode else "sk"
        self.stat_captions = []
        self.stat_cards = {}
        self.active_filter = "total"
        self.result_exporter = ResultExporter()
        self.stats_box = None
        self.resize(1500, 920)
        self._apply_window_icon()
        self._build_ui()
        self._update_texts()
        self._apply_theme()

    def _apply_window_icon(self):
        icon_path = self.assets_dir / "orimslav_logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)

        self.logo_label = QLabel("")
        self.logo_label.setFixedSize(180, 64)
        self.logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._update_logo()

        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-size: 30px; font-weight: 800; color: #0f172a;")
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("font-size: 15px; color: #475569;")

        header_text_layout.addWidget(self.title_label)
        header_text_layout.addWidget(self.subtitle_label)
        header_layout.addWidget(self.logo_label, 0, Qt.AlignTop)
        header_layout.addLayout(header_text_layout, 1)
        root.addLayout(header_layout)

        toolbar = QHBoxLayout()
        self.import_button = QPushButton("")
        self.import_button.clicked.connect(self.import_csv)
        self.sample_csv_button = QPushButton("")
        self.sample_csv_button.clicked.connect(self.save_sample_csv)
        self.check_button = QPushButton("")
        self.check_button.clicked.connect(self.start_check)
        self.check_button.setEnabled(self.demo_mode)
        self.fix_button = QPushButton("")
        self.fix_button.clicked.connect(self.fix_selected_camera)
        self.fix_button.setEnabled(False)
        self.recheck_button = QPushButton("")
        self.recheck_button.clicked.connect(self.recheck_selected_camera)
        self.recheck_button.setEnabled(False)
        self.export_csv_button = QPushButton("")
        self.export_csv_button.clicked.connect(self.export_results_csv)
        self.export_csv_button.setEnabled(False)
        self.export_excel_button = QPushButton("")
        self.export_excel_button.clicked.connect(self.export_results_excel)
        self.export_excel_button.setEnabled(False)
        self.settings_button = QPushButton("")
        self.settings_button.clicked.connect(self.open_settings)
        self.theme_button = QPushButton("")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.sk_button = QPushButton("")
        self.sk_button.setProperty("variant", "language")
        self.sk_button.setIcon(self._create_flag_icon("sk"))
        self.sk_button.setIconSize(QSize(28, 20))
        self.sk_button.clicked.connect(lambda: self.set_language("sk"))
        self.sk_button.setFixedSize(46, 34)
        self.en_button = QPushButton("")
        self.en_button.setProperty("variant", "language")
        self.en_button.setIcon(self._create_flag_icon("en"))
        self.en_button.setIconSize(QSize(28, 20))
        self.en_button.clicked.connect(lambda: self.set_language("en"))
        self.en_button.setFixedSize(46, 34)

        toolbar.addWidget(self.import_button)
        toolbar.addWidget(self.sample_csv_button)
        toolbar.addWidget(self.check_button)
        toolbar.addWidget(self.fix_button)
        toolbar.addWidget(self.recheck_button)
        toolbar.addWidget(self.export_csv_button)
        toolbar.addWidget(self.export_excel_button)
        toolbar.addWidget(self.settings_button)
        toolbar.addStretch()
        toolbar.addWidget(self.sk_button)
        toolbar.addWidget(self.en_button)
        toolbar.addWidget(self.theme_button)
        root.addLayout(toolbar)

        self.csv_label = QLabel("")
        self.csv_label.setMinimumHeight(40)
        root.addWidget(self.csv_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.stats_box = QGroupBox("")
        stats_layout = QGridLayout(self.stats_box)
        self.stat_total = ClickableLabel("0")
        self.stat_ok = ClickableLabel("0")
        self.stat_problem = ClickableLabel("0")
        self.stat_auth = ClickableLabel("0")
        self.stat_skipped = ClickableLabel("0")
        labels = [
            ("total", self.stat_total, "#eef4ff", "#174ea6"),
            ("ok", self.stat_ok, "#e9f9ef", "#187234"),
            ("problems", self.stat_problem, "#fff4de", "#9a5b00"),
            ("auth_failed", self.stat_auth, "#ffecec", "#b42318"),
            ("skipped", self.stat_skipped, "#edf1f7", "#475569"),
        ]
        for index, (filter_key, value_label, background, color) in enumerate(labels):
            caption = ClickableLabel("")
            caption.setStyleSheet("font-size: 14px; font-weight: 700; color: #334155;")
            self.stat_captions.append(caption)
            caption.setCursor(Qt.PointingHandCursor)
            value_label.setCursor(Qt.PointingHandCursor)
            caption.clicked.connect(lambda _checked=False, key=filter_key: self._set_filter(key))
            value_label.clicked.connect(lambda _checked=False, key=filter_key: self._set_filter(key))
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setMinimumHeight(58)
            value_label.setStyleSheet(
                f"font-size: 28px; font-weight: 800; padding: 8px; background: {background}; "
                f"color: {color}; border: 1px solid #b8c4d1; border-radius: 8px;"
            )
            self.stat_cards[filter_key] = {
                "caption": caption,
                "value": value_label,
                "light_background": background,
                "light_text": color,
            }
            stats_layout.addWidget(caption, 0, index)
            stats_layout.addWidget(value_label, 1, index)
        root.addWidget(self.stats_box)

        self.table = QTableWidget(0, 7)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(1, 290)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 180)
        root.addWidget(self.table, 3)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(160)
        self.details.setMaximumHeight(230)
        root.addWidget(self.details, 1)

        if self.demo_mode:
            self.import_button.setEnabled(False)
            self.sample_csv_button.setEnabled(False)
            self.sk_button.setEnabled(False)
            self.en_button.setEnabled(False)

    def _apply_theme(self):
        app = QApplication.instance()
        if app is None:
            return

        if self.dark_mode:
            app.setStyleSheet(DARK_STYLESHEET)
            self.csv_label.setStyleSheet(
                "padding: 10px 12px; background: #111827; color: #e5e7eb; "
                "border: 1px solid #334155; border-radius: 6px;"
            )
        else:
            app.setStyleSheet(LIGHT_STYLESHEET)
            self.csv_label.setStyleSheet(
                "padding: 10px 12px; background: white; color: #14213d; "
                "border: 1px solid #b8c4d1; border-radius: 6px;"
            )

        self._update_texts()
        self._update_header_styles()
        self._update_stat_card_styles()
        self._refresh_table()

    def _update_header_styles(self):
        if self.dark_mode:
            self.title_label.setStyleSheet("font-size: 30px; font-weight: 800; color: #f8fafc;")
            self.subtitle_label.setStyleSheet("font-size: 15px; color: #94a3b8;")
            for caption in self.stat_captions:
                caption.setStyleSheet("font-size: 14px; font-weight: 700; color: #e5e7eb;")
        else:
            self.title_label.setStyleSheet("font-size: 30px; font-weight: 800; color: #0f172a;")
            self.subtitle_label.setStyleSheet("font-size: 15px; color: #475569;")
            for caption in self.stat_captions:
                caption.setStyleSheet("font-size: 14px; font-weight: 700; color: #334155;")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()

    def set_language(self, language: str):
        if language == self.language:
            return
        self.language = language
        self._update_texts()
        self._refresh_table()

    def tr(self, key: str, **kwargs):
        text = TRANSLATIONS[self.language][key]
        return text.format(**kwargs) if kwargs else text

    def _status_label(self, status_key: str) -> str:
        mapping = {
            "ok": self.tr("ok"),
            "problem": self.tr("status_problem"),
            "auth_failed": self.tr("auth_failed"),
            "skipped": self.tr("skipped"),
        }
        return mapping[status_key]

    def _update_texts(self):
        self.setWindowTitle(self.tr("app_title"))
        self.title_label.setText(self.tr("app_title"))
        self.subtitle_label.setText(self.tr("subtitle"))
        self.import_button.setText(self.tr("import_csv"))
        self.sample_csv_button.setText(self.tr("sample_csv"))
        self.check_button.setText(self.tr("start_check"))
        self.fix_button.setText(self.tr("open_browser"))
        self.recheck_button.setText(self.tr("recheck"))
        self.export_csv_button.setText(self.tr("export_csv"))
        self.export_excel_button.setText(self.tr("export_excel"))
        self.settings_button.setText(self.tr("settings_button"))
        self.theme_button.setText(self.tr("theme_light") if self.dark_mode else self.tr("theme_dark"))
        self.sk_button.setToolTip(self.tr("flag_sk_tooltip"))
        self.en_button.setToolTip(self.tr("flag_en_tooltip"))
        self._update_language_buttons()
        self.stats_box.setTitle(self.tr("summary"))
        self.table.setHorizontalHeaderLabels(TRANSLATIONS[self.language]["headers"])
        self.details.setPlaceholderText(self.tr("details_placeholder"))
        for filter_key, widgets in self.stat_cards.items():
            widgets["caption"].setText(self.tr(filter_key))
        self._update_csv_label()

    def _update_language_buttons(self):
        self.sk_button.setProperty("active", "true" if self.language == "sk" else "false")
        self.en_button.setProperty("active", "true" if self.language == "en" else "false")
        for button in (self.sk_button, self.en_button):
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _update_logo(self):
        logo_path = self.assets_dir / "orimslav_logo_blue_transparent.png"
        if not logo_path.exists():
            self.logo_label.clear()
            return

        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            self.logo_label.clear()
            return

        scaled = pixmap.scaled(
            self.logo_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.logo_label.setPixmap(scaled)

    def _create_flag_icon(self, language: str) -> QIcon:
        pixmap = QPixmap(28, 20)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        renderer = QSvgRenderer(QByteArray(self._flag_svg(language).encode("utf-8")))
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    def _flag_svg(self, language: str) -> str:
        if language == "sk":
            return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 20">
<rect width="28" height="20" rx="1.5" fill="#ffffff"/>
<rect y="6.67" width="28" height="6.66" fill="#0B4EA2"/>
<rect y="13.33" width="28" height="6.67" fill="#EE1C25"/>
<path d="M5.2 3.2h5.8c1.15 0 2.1.94 2.1 2.1v4.25c0 3.25-2.45 5.42-5 6.63-2.55-1.21-5-3.38-5-6.63V5.3c0-1.16.95-2.1 2.1-2.1Z" fill="#ffffff"/>
<path d="M5.7 3.8h4.8c1.12 0 2.03.91 2.03 2.03v3.92c0 2.92-2.2 4.88-4.43 5.96-2.23-1.08-4.43-3.04-4.43-5.96V5.83c0-1.12.91-2.03 2.03-2.03Z" fill="#EE1C25"/>
<rect x="7.25" y="5.1" width="1.7" height="5.1" rx=".2" fill="#ffffff"/>
<rect x="5.6" y="6.85" width="5.05" height="1.55" rx=".2" fill="#ffffff"/>
<path d="M5.05 10.8c1.05-.2 1.9-.76 2.55-1.6.75.99 1.85 1.58 3.3 1.75-.24.36-.39.7-.46 1.03-.9-.22-1.67-.62-2.34-1.23-.63.58-1.48 1.01-2.57 1.28-.05-.4-.24-.81-.48-1.2Z" fill="#0B4EA2"/>
<path d="M4.8 12.15c1.1-.1 2.06-.48 2.82-1.14.76.66 1.72 1.04 2.82 1.14-.12.26-.2.51-.25.76-.98-.14-1.84-.47-2.57-.98-.73.51-1.59.84-2.57.98-.05-.25-.13-.5-.25-.76Z" fill="#0B4EA2"/>
<path d="M4.65 13.3c1.22-.06 2.2-.33 2.97-.8.77.47 1.75.74 2.97.8-.71.92-1.67 1.65-2.97 2.29-1.3-.64-2.26-1.37-2.97-2.29Z" fill="#0B4EA2"/>
<rect x=".5" y=".5" width="27" height="19" rx="1" fill="none" stroke="#334155"/>
</svg>"""
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 20">
<rect width="28" height="20" rx="1.5" fill="#012169"/>
<path d="M0 0 28 20M28 0 0 20" stroke="#ffffff" stroke-width="5"/>
<path d="M0 0 28 20M28 0 0 20" stroke="#C8102E" stroke-width="2.2"/>
<path d="M14 0v20M0 10h28" stroke="#ffffff" stroke-width="6"/>
<path d="M14 0v20M0 10h28" stroke="#C8102E" stroke-width="3.2"/>
<rect x=".5" y=".5" width="27" height="19" rx="1" fill="none" stroke="#334155"/>
</svg>"""

    def _update_csv_label(self):
        if self.demo_mode:
            self.csv_label.setText("DEMO MODE — synthetic data on 192.0.2.0/24 (RFC 5737). No real cameras contacted.")
            return
        if self.csv_path:
            cameras_count = len(CSVLoader(self.csv_path).load_cameras())
            self.csv_label.setText(self.tr("csv_loaded", path=Path(self.csv_path), count=cameras_count))
        else:
            self.csv_label.setText(self.tr("csv_missing"))

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("file_dialog_csv_title"), "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            loader = CSVLoader(path)
            cameras = loader.load_cameras()
        except Exception as exc:
            QMessageBox.critical(self, self.tr("import_failed"), str(exc))
            return

        self.csv_path = path
        self.csv_label.setText(self.tr("csv_loaded", path=Path(path), count=len(cameras)))
        self.check_button.setEnabled(True)
        self.results = []
        self.displayed_results = []
        self.summary = {}
        self.active_filter = "total"
        self._populate_table([])
        self._update_stats({})
        self._update_export_buttons()
        self.details.clear()

    def open_settings(self):
        dialog = SettingsDialog(self, translator=self.tr)
        dialog.exec()

    def save_sample_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("save_sample_csv_title"),
            self.tr("sample_csv_default_name"),
            "CSV Files (*.csv)",
        )
        if not path:
            return

        try:
            Path(path).write_text(self._sample_csv_content(), encoding="utf-8-sig")
            self.details.setPlainText(self.tr("sample_csv_help"))
            QMessageBox.information(self, self.tr("sample_csv"), self.tr("sample_csv_saved", path=Path(path)))
        except Exception as exc:
            QMessageBox.critical(self, self.tr("sample_csv_failed"), str(exc))

    def start_check(self):
        if not self.csv_path:
            QMessageBox.warning(self, self.tr("error"), self.tr("import_first"))
            return

        self.progress.setValue(0)
        self.import_button.setEnabled(False)
        self.check_button.setEnabled(False)
        self.fix_button.setEnabled(False)
        self.recheck_button.setEnabled(False)
        self.worker = CheckWorker(self.csv_path, demo_mode=self.demo_mode)
        self.worker.progress_changed.connect(self._on_progress_changed)
        self.worker.finished_with_results.connect(self._on_check_finished)
        self.worker.failed.connect(self._on_check_failed)
        self.worker.start()

    def _on_progress_changed(self, done: int, total: int, camera_result: dict):
        percentage = int(done * 100 / total) if total else 0
        self.progress.setValue(percentage)
        self.details.setPlainText(
            self.tr("checking_progress", done=done, total=total, ip=camera_result.get("ip", ""))
        )

    def _on_check_finished(self, results: list, summary: dict):
        self.results = results
        self.summary = summary
        self.import_button.setEnabled(not self.demo_mode)
        self.check_button.setEnabled(True)
        self._update_stats(summary)
        self._refresh_table()
        self._update_export_buttons()
        self.details.setPlainText(self.tr("check_finished"))

    def _on_check_failed(self, error: str):
        self.import_button.setEnabled(not self.demo_mode)
        self.check_button.setEnabled(True)
        self._update_export_buttons()
        QMessageBox.critical(self, self.tr("check_failed"), error)

    def _update_stats(self, summary: dict):
        self.stat_total.setText(str(summary.get("total", 0)))
        self.stat_ok.setText(str(summary.get("ok", 0)))
        self.stat_problem.setText(str(summary.get("problems", 0)))
        self.stat_auth.setText(str(summary.get("auth_failed", 0)))
        self.stat_skipped.setText(str(summary.get("skipped", 0)))

    def _populate_table(self, rows: list):
        self.displayed_results = list(rows)
        self.table.setSortingEnabled(False)
        self.table.clearSelection()
        self.table.setRowCount(len(rows))
        for row_index, camera in enumerate(rows):
            status_key = self._camera_status_key(camera)
            status = self._status_label(status_key)
            issues = ", ".join(camera.get("issues", [])) or camera.get("skip_reason", "")
            values = [
                (camera.get("ip", ""), self._ip_sort_key(camera.get("ip", ""))),
                camera.get("name", ""),
                camera.get("vendor", ""),
                camera.get("model", "") or "",
                status,
                camera.get("current_time", "") or "",
                issues,
            ]
            for column_index, value in enumerate(values):
                sort_value = None
                if isinstance(value, tuple):
                    display_value, sort_value = value
                else:
                    display_value = value
                item = SortableTableWidgetItem(str(display_value), sort_value=sort_value)
                item.setData(Qt.UserRole, camera)
                self._style_table_item(item, status_key)
                self.table.setItem(row_index, column_index, item)
        self.table.resizeRowsToContents()
        self.table.setSortingEnabled(True)

    def _style_table_item(self, item: QTableWidgetItem, status_key: str):
        if self.dark_mode:
            item.setForeground(QColor("#e5e7eb"))
            if status_key == "ok":
                item.setBackground(QColor("#10261a"))
            elif status_key == "problem":
                item.setBackground(QColor("#2b1d12"))
            elif status_key == "auth_failed":
                item.setBackground(QColor("#2f1418"))
            elif status_key == "skipped":
                item.setBackground(QColor("#1e293b"))
        else:
            item.setForeground(QColor("#111827"))
            if status_key == "ok":
                item.setBackground(QColor("#f0fdf4"))
            elif status_key == "problem":
                item.setBackground(QColor("#fff7ed"))
            elif status_key == "auth_failed":
                item.setBackground(QColor("#fef2f2"))
            elif status_key == "skipped":
                item.setBackground(QColor("#f1f5f9"))

    def _camera_status_key(self, camera: dict) -> str:
        if camera.get("skipped"):
            return "skipped"
        if not camera.get("auth_ok"):
            return "auth_failed"
        if camera.get("issues"):
            return "problem"
        return "ok"

    def _on_selection_changed(self):
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.fix_button.setEnabled(has_selection and bool(self.csv_path))
        self.recheck_button.setEnabled(has_selection and bool(self.csv_path))
        if not has_selection:
            return
        camera = self._selected_camera()
        if camera:
            detail_lines = [
                f"{self.tr('camera_ip')}: {camera.get('ip', '')}",
                f"{self.tr('camera_name')}: {camera.get('name', '')}",
                f"{self.tr('camera_vendor')}: {camera.get('vendor', '')}",
                f"{self.tr('camera_model')}: {camera.get('model', '')}",
                f"{self.tr('camera_status')}: {self._status_label(self._camera_status_key(camera))}",
                f"{self.tr('camera_time')}: {camera.get('current_time', '')}",
                f"{self.tr('camera_time_diff')}: {camera.get('time_diff', '')}",
                "",
                f"{self.tr('camera_issues')}:",
            ]
            issue_list = camera.get("issues", []) or [camera.get("skip_reason", self.tr("no_details"))]
            detail_lines.extend(f"- {issue}" for issue in issue_list)
            self.details.setPlainText("\n".join(detail_lines))

    def _selected_camera(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        item = self.table.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def recheck_selected_camera(self):
        camera = self._selected_camera()
        if not camera:
            return
        try:
            checker = DemoCameraChecker() if self.demo_mode else CameraChecker(self.csv_path)
            camera_data = checker.csv_loader.get_camera_by_ip(camera["ip"])
            if not camera_data:
                raise ValueError(self.tr("camera_not_found"))
            updated = checker.check_camera(camera_data)
            self._replace_result(updated)
            self.details.setPlainText(self.tr("recheck_done", ip=camera["ip"]))
        except Exception as exc:
            QMessageBox.critical(self, self.tr("recheck_failed"), str(exc))

    def fix_selected_camera(self):
        camera = self._selected_camera()
        if not camera:
            return
        url = f"http://{camera['ip']}"
        opened = webbrowser.open(url)
        if not opened:
            QMessageBox.warning(
                self,
                self.tr("open_failed"),
                self.tr("open_failed_message", ip=camera["ip"], url=url),
            )
            return

        self.details.setPlainText(self.tr("browser_opened", ip=camera["ip"], url=url))

    def _replace_result(self, updated_camera: dict):
        for index, result in enumerate(self.results):
            if result.get("ip") == updated_camera.get("ip"):
                self.results[index] = updated_camera
                break
        checker = DemoCameraChecker() if self.demo_mode else CameraChecker(self.csv_path)
        self.summary = checker.summarize(self.results)
        self._update_stats(self.summary)
        self._refresh_table()

    def _set_filter(self, filter_key: str):
        self.active_filter = filter_key
        self._update_stat_card_styles()
        self._refresh_table()

    def _refresh_table(self):
        self._populate_table(self._filtered_results())
        self._on_selection_changed()
        self._update_export_buttons()

    def _filtered_results(self):
        if self.active_filter == "ok":
            return [camera for camera in self.results if self._camera_status_key(camera) == "ok"]
        if self.active_filter == "problems":
            return [camera for camera in self.results if self._camera_status_key(camera) == "problem"]
        if self.active_filter == "auth_failed":
            return [camera for camera in self.results if self._camera_status_key(camera) == "auth_failed"]
        if self.active_filter == "skipped":
            return [camera for camera in self.results if self._camera_status_key(camera) == "skipped"]
        return list(self.results)

    def _update_stat_card_styles(self):
        active_border = "#60a5fa" if self.dark_mode else "#1d4ed8"
        inactive_border = "#334155" if self.dark_mode else "#b8c4d1"

        for filter_key, widgets in self.stat_cards.items():
            if self.dark_mode:
                palette = {
                    "total": ("#172554", "#dbeafe"),
                    "ok": ("#052e16", "#dcfce7"),
                    "problems": ("#3b1d0f", "#ffedd5"),
                    "auth_failed": ("#3a1016", "#fee2e2"),
                    "skipped": ("#1e293b", "#e2e8f0"),
                }
                background, text_color = palette[filter_key]
            else:
                background = widgets["light_background"]
                text_color = widgets["light_text"]

            border_color = active_border if filter_key == self.active_filter else inactive_border
            widgets["value"].setStyleSheet(
                f"font-size: 28px; font-weight: 800; padding: 8px; background: {background}; "
                f"color: {text_color}; border: 2px solid {border_color}; border-radius: 8px;"
            )

    def _ip_sort_key(self, ip_address: str):
        parts = str(ip_address).split(".")
        if len(parts) != 4:
            return (999, 999, 999, 999)
        try:
            return tuple(int(part) for part in parts)
        except ValueError:
            return (999, 999, 999, 999)

    def _update_export_buttons(self):
        has_rows = bool(self.displayed_results)
        self.export_csv_button.setEnabled(has_rows)
        self.export_excel_button.setEnabled(has_rows)

    def export_results_csv(self):
        rows = self._filtered_results()
        if not rows:
            QMessageBox.information(self, self.tr("export_csv_title"), self.tr("no_results_export_csv"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("save_csv_title"),
            self._default_export_name("csv"),
            "CSV Files (*.csv)",
        )
        if not path:
            return

        try:
            self.result_exporter.export_csv(path, rows, self.language)
            self.details.setPlainText(self.tr("csv_exported", path=Path(path)))
        except Exception as exc:
            QMessageBox.critical(self, self.tr("csv_export_failed"), str(exc))

    def export_results_excel(self):
        rows = self._filtered_results()
        if not rows:
            QMessageBox.information(self, self.tr("export_excel_title"), self.tr("no_results_export_excel"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("save_excel_title"),
            self._default_export_name("excel"),
            "Excel Files (*.xlsx)",
        )
        if not path:
            return

        path = self._normalize_excel_export_path(path)

        try:
            self.result_exporter.export_excel(path, rows, self.language)
            self.details.setPlainText(self.tr("excel_exported", path=Path(path)))
        except ModuleNotFoundError:
            QMessageBox.critical(
                self,
                self.tr("excel_export_failed"),
                self.tr("missing_openpyxl"),
            )
        except Exception as exc:
            QMessageBox.critical(self, self.tr("excel_export_failed"), str(exc))

    def _default_export_name(self, export_type: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if export_type == "excel":
            return self.tr("excel_default_name", timestamp=timestamp)
        return self.tr("csv_default_name", timestamp=timestamp)

    def _normalize_excel_export_path(self, path: str) -> str:
        export_path = Path(path)
        if not export_path.suffix:
            return str(export_path.with_suffix(".xlsx"))
        if export_path.suffix.lower() == ".xls":
            return str(export_path.with_suffix(".xlsx"))
        return str(export_path)

    def _sample_csv_content(self) -> str:
        return "\n".join(
            [
                "Web Site,Login Name,Password,Account,Comments",
                "http://192.168.1.100,admin,admin123,Predna brana,IPC-HDW1234T-ZS",
                "http://192.168.1.101,admin,heslo456,Sklad,IPC-HFW2841T-AS",
            ]
        )


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    demo_mode = "--demo" in argv
    qt_argv = [sys.argv[0]] + [arg for arg in argv if arg != "--demo"]
    app = QApplication(qt_argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 11))
    window = MainWindow(demo_mode=demo_mode)
    window.show()
    sys.exit(app.exec())
