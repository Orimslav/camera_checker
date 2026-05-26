from typing import Callable, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from dahuawin import config, settings_store


_DST_START_KEYS = ("DSTStart.Month", "DSTStart.Week", "DSTStart.Day", "DSTStart.Hour")
_DST_END_KEYS = ("DSTEnd.Month", "DSTEnd.Week", "DSTEnd.Day", "DSTEnd.Hour")


class SettingsDialog(QDialog):
    def __init__(self, parent=None, translator: Optional[Callable[[str], str]] = None):
        super().__init__(parent)
        self.tr_ = translator or (lambda key: key)
        self.setWindowTitle(self.tr_("settings_title"))
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        root.setSpacing(12)

        root.addWidget(self._build_ntp_group())
        root.addWidget(self._build_dst_group())
        root.addWidget(self._build_tolerance_group())

        footer = QHBoxLayout()
        reset_btn = QPushButton(self.tr_("settings_reset"))
        reset_btn.clicked.connect(self._reset_to_defaults)
        footer.addWidget(reset_btn)
        footer.addStretch()
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText(self.tr_("settings_save"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(self.tr_("settings_cancel"))
        self.buttons.accepted.connect(self._on_save)
        self.buttons.rejected.connect(self.reject)
        footer.addWidget(self.buttons)
        root.addLayout(footer)

        self._load_values(from_defaults=False)

    def _build_ntp_group(self) -> QGroupBox:
        group = QGroupBox(self.tr_("settings_ntp"))
        layout = QVBoxLayout(group)

        layout.addWidget(QLabel(self.tr_("settings_ntp_addresses")))
        self.ntp_list = QListWidget()
        self.ntp_list.setMaximumHeight(110)
        layout.addWidget(self.ntp_list)

        list_buttons = QHBoxLayout()
        add_btn = QPushButton(self.tr_("settings_add"))
        add_btn.clicked.connect(self._add_address)
        remove_btn = QPushButton(self.tr_("settings_remove"))
        remove_btn.clicked.connect(self._remove_address)
        list_buttons.addWidget(add_btn)
        list_buttons.addWidget(remove_btn)
        list_buttons.addStretch()
        layout.addLayout(list_buttons)

        form = QFormLayout()
        self.ntp_port_edit = QLineEdit()
        self.ntp_port_edit.setMaximumWidth(100)
        form.addRow(self.tr_("settings_ntp_port"), self.ntp_port_edit)
        self.ntp_enable_check = QCheckBox()
        form.addRow(self.tr_("settings_ntp_enable"), self.ntp_enable_check)
        layout.addLayout(form)

        return group

    def _build_dst_group(self) -> QGroupBox:
        group = QGroupBox(self.tr_("settings_dst"))
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        self.dst_enable_check = QCheckBox(self.tr_("settings_dst_enable"))
        grid.addWidget(self.dst_enable_check, 0, 0, 1, 5)

        grid.addWidget(QLabel(""), 1, 0)
        grid.addWidget(QLabel(self.tr_("settings_dst_month")), 1, 1)
        grid.addWidget(QLabel(self.tr_("settings_dst_week")), 1, 2)
        grid.addWidget(QLabel(self.tr_("settings_dst_day")), 1, 3)
        grid.addWidget(QLabel(self.tr_("settings_dst_hour")), 1, 4)

        self.dst_fields = {}
        grid.addWidget(QLabel(self.tr_("settings_dst_start")), 2, 0)
        for col, key in enumerate(_DST_START_KEYS):
            edit = QLineEdit()
            edit.setMaximumWidth(70)
            self.dst_fields[key] = edit
            grid.addWidget(edit, 2, col + 1)

        grid.addWidget(QLabel(self.tr_("settings_dst_end")), 3, 0)
        for col, key in enumerate(_DST_END_KEYS):
            edit = QLineEdit()
            edit.setMaximumWidth(70)
            self.dst_fields[key] = edit
            grid.addWidget(edit, 3, col + 1)

        hint = QLabel(self.tr_("settings_dst_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        grid.addWidget(hint, 4, 0, 1, 5)

        return group

    def _build_tolerance_group(self) -> QGroupBox:
        group = QGroupBox(self.tr_("settings_tolerance"))
        form = QFormLayout(group)
        self.time_diff_spin = QSpinBox()
        self.time_diff_spin.setRange(0, 3600)
        self.time_diff_spin.setSuffix(" s")
        form.addRow(self.tr_("settings_max_time_diff"), self.time_diff_spin)
        return group

    def _load_values(self, from_defaults: bool):
        if from_defaults:
            addresses = list(config.EXPECTED_NTP_ADDRESSES)
            port = config.EXPECTED_NTP_PORT
            enable = config.EXPECTED_NTP_ENABLE
            dst = dict(config.EXPECTED_DST)
            time_diff = config.MAX_TIME_DIFF_SECONDS
        else:
            addresses = settings_store.expected_ntp_addresses()
            port = settings_store.expected_ntp_port()
            enable = settings_store.expected_ntp_enable()
            dst = settings_store.expected_dst()
            time_diff = settings_store.max_time_diff_seconds()

        self.ntp_list.clear()
        for addr in addresses:
            self.ntp_list.addItem(addr)
        self.ntp_port_edit.setText(str(port))
        self.ntp_enable_check.setChecked(bool(enable))
        self.dst_enable_check.setChecked(str(dst.get("DSTEnable", "true")).lower() in ("1", "true"))
        for key, edit in self.dst_fields.items():
            edit.setText(str(dst.get(key, "")))
        self.time_diff_spin.setValue(int(time_diff))

    def _add_address(self):
        text, ok = QInputDialog.getText(self, self.tr_("settings_add"), self.tr_("settings_ntp_address_prompt"))
        if ok and text.strip():
            self.ntp_list.addItem(text.strip())

    def _remove_address(self):
        for item in self.ntp_list.selectedItems():
            self.ntp_list.takeItem(self.ntp_list.row(item))

    def _reset_to_defaults(self):
        self._load_values(from_defaults=True)

    def _on_save(self):
        addresses = [self.ntp_list.item(i).text().strip() for i in range(self.ntp_list.count())]
        addresses = [addr for addr in addresses if addr]
        if not addresses:
            QMessageBox.warning(self, self.tr_("settings_title"), self.tr_("settings_need_address"))
            return

        port = self.ntp_port_edit.text().strip()
        if not port.isdigit():
            QMessageBox.warning(self, self.tr_("settings_title"), self.tr_("settings_port_invalid"))
            return

        dst = {"DSTEnable": "true" if self.dst_enable_check.isChecked() else "false"}
        for key, edit in self.dst_fields.items():
            dst[key] = edit.text().strip()

        settings_store.save_settings(
            ntp_addresses=addresses,
            ntp_port=port,
            ntp_enable=self.ntp_enable_check.isChecked(),
            dst=dst,
            max_time_diff=self.time_diff_spin.value(),
        )
        self.accept()
