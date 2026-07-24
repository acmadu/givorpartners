"""Ödeme öncesinde müşteri bilgileri alma."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QLabel,
)


class CustomerInfoDialog(QDialog):
    """Ödeme öncesinde müşteri bilgileri."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Müşteri Bilgileri")
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Başlık
        title = QLabel("Müşteri Bilgilerini Girin")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        subtitle = QLabel("İsteğe bağlı — boş bırakıp 'Atla' diyebilirsiniz.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # Form
        form = QFormLayout()
        form.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("İsim")
        self.name.setFocus()
        form.addRow("Adı:", self.name)

        self.surname = QLineEdit()
        self.surname.setPlaceholderText("Soyisim")
        form.addRow("Soyadı:", self.surname)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("5xx xxx xx xx")
        form.addRow("Telefon:", self.phone)

        self.birthdate = QLineEdit()
        self.birthdate.setPlaceholderText("DD.MM.YYYY (İsteğe bağlı)")
        form.addRow("Doğum Tarihi:", self.birthdate)

        self.anniversary = QLineEdit()
        self.anniversary.setPlaceholderText("DD.MM (İsteğe bağlı)")
        form.addRow("Evlilik Yıl Dönümü:", self.anniversary)

        layout.addLayout(form)

        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset
        )
        buttons.button(QDialogButtonBox.Ok).setText("Devam Et")
        buttons.button(QDialogButtonBox.Cancel).setText("Vazgeç")
        skip_btn = buttons.button(QDialogButtonBox.Reset)
        skip_btn.setText("Atla →")
        skip_btn.clicked.connect(self._skip)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _skip(self):
        """Müşteri bilgisi boş bırakılarak ödemeye geç."""
        self.name.clear()
        self.surname.clear()
        self.phone.clear()
        self.birthdate.clear()
        self.anniversary.clear()
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "surname": self.surname.text().strip(),
            "phone": self.phone.text().strip(),
            "birthdate": self.birthdate.text().strip(),
            "anniversary": self.anniversary.text().strip(),
        }
