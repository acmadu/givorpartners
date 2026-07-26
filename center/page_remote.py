"""Uzaktan yönetim ayarları sayfası — Merkez paneli.

Bu sayfadan:
  - Tüm bayilere veya belirli bir bayiye tema, zorunlu sürüm, duyuru gönderilir.
  - Ayarlar MongoDB'deki remote_configs koleksiyonuna kaydedilir.
  - Bayiler programa girdiklerinde bu ayarları otomatik uygular.
"""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QCheckBox, QGroupBox, QMessageBox,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QDialog, QDialogButtonBox,
)
from PyQt5.QtCore import Qt
from pymongo.errors import PyMongoError


class RemoteManagementPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db.db   # pymongo Database nesnesi
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        title = QLabel("Uzaktan Yönetim")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # ── Genel ayarlar (tüm bayiler = "*") ──
        general_box = QGroupBox("Tüm Bayiler — Genel Ayarlar")
        glay = QFormLayout(general_box)
        glay.setContentsMargins(16, 12, 16, 12)
        glay.setSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["(Değişme)", "night_mint", "ocean", "amber", "light"])
        glay.addRow("Zorunlu Tema:", self.theme_combo)

        self.min_version_edit = QLineEdit()
        self.min_version_edit.setPlaceholderText("Örn: 1.1.0  (boş bırakırsan zorunluluk yok)")
        glay.addRow("Minimum Sürüm:", self.min_version_edit)

        self.auto_update_check = QCheckBox("Otomatik sessiz güncelleme (kullanıcı onayı olmadan)")
        glay.addRow("", self.auto_update_check)

        self.announcement_edit = QPlainTextEdit()
        self.announcement_edit.setPlaceholderText(
            "Duyuru metni (boş bırakırsan duyuru yok)")
        self.announcement_edit.setMaximumHeight(80)
        glay.addRow("Duyuru:", self.announcement_edit)

        save_btn = QPushButton("💾  Tüm Bayilere Uygula")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save_general)
        glay.addRow("", save_btn)

        layout.addWidget(general_box)

        # ── Bayi bazlı override ──
        specific_box = QGroupBox("Belirli Bayi — Özel Ayar")
        slay = QFormLayout(specific_box)
        slay.setContentsMargins(16, 12, 16, 12)
        slay.setSpacing(10)

        self.specific_code = QLineEdit()
        self.specific_code.setPlaceholderText("BAYI-001")
        slay.addRow("Bayi Kodu:", self.specific_code)

        self.specific_theme = QComboBox()
        self.specific_theme.addItems(["(Değişme)", "night_mint", "ocean", "amber", "light"])
        slay.addRow("Özel Tema:", self.specific_theme)

        row = QHBoxLayout()
        add_specific_btn = QPushButton("➕ Kaydet")
        add_specific_btn.clicked.connect(self._save_specific)
        remove_specific_btn = QPushButton("🗑 Kaldır", objectName="danger")
        remove_specific_btn.clicked.connect(self._remove_specific)
        row.addWidget(add_specific_btn)
        row.addWidget(remove_specific_btn)
        row.addStretch()
        slay.addRow("", row)

        layout.addWidget(specific_box)

        # ── Mevcut kayıtlar tablosu ──
        layout.addWidget(QLabel("<b>Mevcut Uzaktan Ayarlar:</b>"))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Hedef", "Tema", "Min Sürüm", "Otomatik Güncelleme", "Duyuru"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn, 0, Qt.AlignLeft)

    def _save_general(self):
        data: dict = {"target": "*"}
        theme = self.theme_combo.currentText()
        if theme != "(Değişme)":
            data["theme"] = theme
        else:
            data["theme"] = None

        min_ver = self.min_version_edit.text().strip()
        data["min_version"] = min_ver if min_ver else None

        data["auto_update"] = self.auto_update_check.isChecked()

        ann = self.announcement_edit.toPlainText().strip()
        data["announcement"] = ann if ann else None

        try:
            self.db["remote_configs"].replace_one(
                {"target": "*"}, data, upsert=True
            )
            QMessageBox.information(self, "Kaydedildi",
                                    "Genel uzaktan ayarlar güncellendi.\n"
                                    "Bayiler programı yeniden açtığında uygulanacak.")
            self.refresh()
        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _save_specific(self):
        code = self.specific_code.text().strip().upper()
        if not code:
            QMessageBox.warning(self, "Bayi Kodu Gerekli", "Lütfen bayi kodunu girin.")
            return

        data: dict = {"target": code}
        theme = self.specific_theme.currentText()
        data["theme"] = theme if theme != "(Değişme)" else None

        try:
            self.db["remote_configs"].replace_one(
                {"target": code}, data, upsert=True
            )
            QMessageBox.information(self, "Kaydedildi", f"{code} için özel ayar kaydedildi.")
            self.refresh()
        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _remove_specific(self):
        code = self.specific_code.text().strip().upper()
        if not code:
            QMessageBox.warning(self, "Bayi Kodu Gerekli", "Lütfen bayi kodunu girin.")
            return
        try:
            self.db["remote_configs"].delete_one({"target": code})
            QMessageBox.information(self, "Silindi", f"{code} için özel ayar kaldırıldı.")
            self.refresh()
        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def refresh(self):
        try:
            docs = list(self.db["remote_configs"].find({}, {"_id": 0}))
        except Exception:
            docs = []

        self.table.setRowCount(len(docs))
        for row, doc in enumerate(docs):
            self.table.setItem(row, 0, QTableWidgetItem(doc.get("target", "")))
            self.table.setItem(row, 1, QTableWidgetItem(doc.get("theme") or "—"))
            self.table.setItem(row, 2, QTableWidgetItem(doc.get("min_version") or "—"))
            self.table.setItem(row, 3, QTableWidgetItem(
                "✅ Evet" if doc.get("auto_update") else "Hayır"))
            self.table.setItem(row, 4, QTableWidgetItem(
                (doc.get("announcement") or "")[:60] or "—"))

        # Genel (*) ayarlarını forma yükle
        wildcard = self.db["remote_configs"].find_one({"target": "*"}) if docs else None
        if wildcard:
            theme = wildcard.get("theme") or "(Değişme)"
            idx = self.theme_combo.findText(theme)
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
            self.min_version_edit.setText(wildcard.get("min_version") or "")
            self.auto_update_check.setChecked(bool(wildcard.get("auto_update")))
            self.announcement_edit.setPlainText(wildcard.get("announcement") or "")
