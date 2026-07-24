"""Bayi yönetimi sayfası — bayi kartları ve kasa giriş hesapları."""
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)
from pymongo.errors import DuplicateKeyError, PyMongoError

from common.database import make_password_record


class DealerDialog(QDialog):
    def __init__(self, parent=None, dealer: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Bayi Düzenle" if dealer else "Yeni Bayi")
        self.setMinimumWidth(420)
        dealer = dealer or {}
        self._has_account = bool(dealer.get("username"))

        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        self.code = QLineEdit(dealer.get("code", ""))
        self.code.setPlaceholderText("Örn: BAYI-001")
        self.code.setEnabled(not dealer)  # kod sonradan değiştirilemez
        self.name = QLineEdit(dealer.get("name", ""))
        self.address = QLineEdit(dealer.get("address", ""))
        self.phone = QLineEdit(dealer.get("phone", ""))
        self.username = QLineEdit(dealer.get("username", ""))
        self.username.setPlaceholderText("Kasa girişi için kullanıcı adı")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText(
            "Değiştirmek için yeni şifre yazın" if dealer.get("username")
            else "Kasa giriş şifresi")

        form.addRow("Bayi Kodu:", self.code)
        form.addRow("Bayi Adı:", self.name)
        form.addRow("Adres:", self.address)
        form.addRow("Telefon:", self.phone)
        form.addRow(QLabel("── Kasa Giriş Hesabı ──"))
        form.addRow("Kullanıcı Adı:", self.username)
        form.addRow("Şifre:", self.password)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Kaydet")
        buttons.button(QDialogButtonBox.Cancel).setText("Vazgeç")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validate(self):
        if not self.code.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi",
                                "Bayi kodu ve adı zorunludur.")
            return
        if self.username.text().strip() and not self.password.text() \
                and not self._has_account:
            QMessageBox.warning(self, "Eksik Bilgi",
                                "Yeni hesap için şifre girin.")
            return
        if self.password.text() and len(self.password.text()) < 6:
            QMessageBox.warning(self, "Zayıf Şifre",
                                "Şifre en az 6 karakter olmalıdır.")
            return
        self.accept()

    def dealer_data(self) -> dict:
        """Temel bayi alanlarını döndürür (hesap alanları hariç)."""
        return {
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "address": self.address.text().strip(),
            "phone": self.phone.text().strip(),
        }

    def account_data(self) -> dict:
        """Hesap alanları: kullanıcı adı + (varsa) yeni parola özeti."""
        username = self.username.text().strip()
        if not username:
            return {}
        record = {"username": username}
        if self.password.text():
            record.update(make_password_record(self.password.text()))
        return record

    def account_removed(self) -> bool:
        return self._has_account and not self.username.text().strip()


class DealersPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top = QHBoxLayout()
        title = QLabel("Bayiler", objectName="title")
        add_button = QPushButton("＋ Yeni Bayi", objectName="primary")
        add_button.clicked.connect(self._add_dealer)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(add_button)
        layout.addLayout(top)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Kod", "Bayi Adı", "Adres", "Telefon", "Kasa Hesabı"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._edit_dealer)
        layout.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        edit_button = QPushButton("✏ Düzenle")
        edit_button.clicked.connect(self._edit_dealer)
        delete_button = QPushButton("🗑 Sil", objectName="danger")
        delete_button.clicked.connect(self._delete_dealer)
        bottom.addStretch()
        bottom.addWidget(edit_button)
        bottom.addWidget(delete_button)
        layout.addLayout(bottom)

    def refresh(self):
        dealers = self.db.get_dealers()
        self.table.setRowCount(len(dealers))
        for row, dealer in enumerate(dealers):
            for column, key in enumerate(["code", "name", "address", "phone"]):
                self.table.setItem(
                    row, column, QTableWidgetItem(dealer.get(key, "") or "—"))
            account = dealer.get("username")
            self.table.setItem(row, 4, QTableWidgetItem(
                f"🔑 {account}" if account else "—"))

    def _selected_code(self) -> str:
        row = self.table.currentRow()
        return self.table.item(row, 0).text() if row >= 0 else ""

    def _add_dealer(self):
        dialog = DealerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.dealer_data()
            data.update(dialog.account_data())
            try:
                self.db.add_dealer(data)
            except DuplicateKeyError:
                QMessageBox.warning(
                    self, "Hata",
                    "Bu bayi kodu veya kullanıcı adı zaten kayıtlı.")
            except PyMongoError as error:
                QMessageBox.critical(self, "Veritabanı Hatası",
                                     f"Bayi kaydedilemedi:\n{error}")
            self.refresh()

    def _edit_dealer(self):
        code = self._selected_code()
        if not code:
            QMessageBox.information(self, "Seçim Yok", "Lütfen bir bayi seçin.")
            return
        dealer = self.db.dealers.find_one({"code": code})
        dialog = DealerDialog(self, dealer)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.dealer_data()
            data.update(dialog.account_data())
            try:
                self.db.update_dealer(code, data)
            except DuplicateKeyError:
                QMessageBox.warning(
                    self, "Hata", "Bu kullanıcı adı zaten kayıtlı.")
            except PyMongoError as error:
                QMessageBox.critical(self, "Veritabanı Hatası",
                                     f"Bayi güncellenemedi:\n{error}")
            if dialog.account_removed():
                self.db.remove_dealer_account(code)
            self.refresh()

    def _delete_dealer(self):
        code = self._selected_code()
        if not code:
            QMessageBox.information(self, "Seçim Yok", "Lütfen bir bayi seçin.")
            return
        answer = QMessageBox.question(self, "Bayiyi Sil",
                                      f"'{code}' silinsin mi?")
        if answer == QMessageBox.Yes:
            self.db.delete_dealer(code)
            self.refresh()
