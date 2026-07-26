"""POS terminal ayarları dialog'u — bayi panelinden açılır.

Kasiyer veya yönetici bu dialog'dan:
  • Terminal bağlantı modunu seçer (Manuel / Ingenico / TCP / Seri / Simülasyon)
  • IP adresi, port, seri port ayarlarını girer
  • "Bağlantı Testi" ile mevcut ayarı anında test eder
  • Kaydet ile config.json'a yazar
"""
from __future__ import annotations

import json
import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from common.settings import load_settings, save_settings


# ── Bağlantı testi arka planda ─────────────────────────────────
class _TestWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, settings: dict):
        super().__init__()
        self._settings = settings

    def run(self):
        from pos.payment_terminal import PaymentTerminal
        t = PaymentTerminal(self._settings)
        ok, msg = t.test_connection()
        self.done.emit(ok, msg)


# ── Ana dialog ─────────────────────────────────────────────────
class PosSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("POS Terminal Ayarları")
        self.setMinimumWidth(480)
        self._settings = load_settings()
        self._build_ui()
        self._load_values()

    # ── UI ────────────────────────────────────────────────────
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        lay.addWidget(QLabel("<b>POS Terminal Bağlantı Ayarları</b>"))

        # Mod seçimi
        mode_box = QGroupBox("Bağlantı Modu")
        mlay = QFormLayout(mode_box)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "manual   — Manuel (Kendi kendine gir/onayla)",
            "ingenico — Ingenico iCT/Move serisi (TCP)",
            "tcp      — Genel TCP/IP terminali",
            "serial   — Seri port (USB-RS232)",
            "simulate — Simülasyon (Test modu, gerçek POS yok)",
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mlay.addRow("Mod:", self.mode_combo)
        lay.addWidget(mode_box)

        # TCP / Ingenico ayarları
        self.tcp_box = QGroupBox("TCP / Ağ Bağlantısı")
        tlay = QFormLayout(self.tcp_box)
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("192.168.1.100")
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("8400  (Ingenico varsayılanı)")
        tlay.addRow("Terminal IP:", self.host_edit)
        tlay.addRow("Port:", self.port_edit)
        lay.addWidget(self.tcp_box)

        # Seri port ayarları
        self.serial_box = QGroupBox("Seri Port Bağlantısı")
        slay = QFormLayout(self.serial_box)
        self.serial_port_edit = QLineEdit()
        self.serial_port_edit.setPlaceholderText("COM3  veya  /dev/ttyUSB0")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        slay.addRow("Port:", self.serial_port_edit)
        slay.addRow("Baud:", self.baud_combo)
        lay.addWidget(self.serial_box)

        # Simülasyon bilgisi
        self.sim_box = QGroupBox("Simülasyon Modu")
        sim_lay = QVBoxLayout(self.sim_box)
        sim_info = QLabel(
            "Gerçek bir POS terminali olmadan test edebilirsiniz.\n"
            "Her ödeme isteği için onay/ret seçeneği çıkar.\n"
            "Gerçek kart bilgisi alınmaz, sahte onay kodu üretilir."
        )
        sim_info.setWordWrap(True)
        sim_info.setObjectName("subtitle")
        sim_lay.addWidget(sim_info)
        lay.addWidget(self.sim_box)

        # Bağlantı testi
        test_row = QHBoxLayout()
        self.test_btn = QPushButton("🔌  Bağlantı Testi")
        self.test_btn.clicked.connect(self._test_connection)
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        test_row.addWidget(self.test_btn)
        test_row.addWidget(self.test_result, 1)
        lay.addLayout(test_row)

        # Dialog butonları
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText("💾  Kaydet")
        btns.button(QDialogButtonBox.Cancel).setText("İptal")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    # ── Değerleri forma yükle ─────────────────────────────────
    def _load_values(self):
        mode = self._settings.get("terminal_mode", "manual")
        # simulate modunu da destekle
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemText(i).startswith(mode):
                self.mode_combo.setCurrentIndex(i)
                break

        self.host_edit.setText(self._settings.get("terminal_host", ""))
        port = str(self._settings.get("terminal_tcp_port", "8400"))
        self.port_edit.setText(port)
        self.serial_port_edit.setText(self._settings.get("terminal_port", ""))
        baud = str(self._settings.get("terminal_baud", 9600))
        idx = self.baud_combo.findText(baud)
        if idx >= 0:
            self.baud_combo.setCurrentIndex(idx)

        self._on_mode_changed()

    # ── Mod değişince alanları göster/gizle ──────────────────
    def _on_mode_changed(self):
        mode = self._current_mode()
        self.tcp_box.setVisible(mode in ("ingenico", "tcp"))
        self.serial_box.setVisible(mode == "serial")
        self.sim_box.setVisible(mode == "simulate")
        self.test_btn.setEnabled(mode not in ("manual", "simulate"))
        self.test_result.setText("")

    def _current_mode(self) -> str:
        return self.mode_combo.currentText().split("—")[0].strip()

    # ── Bağlantı testi ───────────────────────────────────────
    def _test_connection(self):
        self.test_result.setText("⏳ Test ediliyor…")
        self.test_btn.setEnabled(False)

        test_settings = dict(self._settings)
        test_settings["terminal_mode"] = self._current_mode()
        test_settings["terminal_host"] = self.host_edit.text().strip()
        try:
            test_settings["terminal_tcp_port"] = int(self.port_edit.text().strip() or "8400")
        except ValueError:
            test_settings["terminal_tcp_port"] = 8400
        test_settings["terminal_port"] = self.serial_port_edit.text().strip()
        test_settings["terminal_baud"] = int(self.baud_combo.currentText())

        self._worker = _TestWorker(test_settings)
        self._worker.done.connect(self._on_test_done)
        self._worker.start()

    def _on_test_done(self, ok: bool, msg: str):
        self.test_btn.setEnabled(True)
        if ok:
            self.test_result.setText(f"✅ {msg}")
            self.test_result.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.test_result.setText(f"❌ {msg}")
            self.test_result.setStyleSheet("color: #c0392b; font-weight: bold;")

    # ── Kaydet ───────────────────────────────────────────────
    def _save(self):
        mode = self._current_mode()
        self._settings["terminal_mode"] = mode
        self._settings["terminal_host"] = self.host_edit.text().strip()
        try:
            self._settings["terminal_tcp_port"] = int(
                self.port_edit.text().strip() or "8400")
        except ValueError:
            QMessageBox.warning(self, "Hatalı Port", "Port geçerli bir sayı olmalı.")
            return
        self._settings["terminal_port"] = self.serial_port_edit.text().strip()
        self._settings["terminal_baud"] = int(self.baud_combo.currentText())

        save_settings(self._settings)
        QMessageBox.information(
            self, "Kaydedildi",
            f"POS ayarları kaydedildi.\n"
            f"Mod: {mode}\n"
            + (f"Terminal: {self._settings['terminal_host']}:{self._settings['terminal_tcp_port']}"
               if mode in ("ingenico", "tcp") else "")
            + ("\n\n⚠ Değişikliğin geçerli olması için programı yeniden başlatın."
               if mode != self._settings.get("terminal_mode") else "")
        )
        self.accept()
