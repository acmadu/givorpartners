"""Kasa giriş ekranı — bayi kullanıcı adı/şifre doğrulaması.

Hesaplar merkez uygulamasındaki Bayiler sayfasından açılır.
Art arda 5 başarısız denemeden sonra giriş 30 saniye kilitlenir
(kaba kuvvet saldırılarını yavaşlatmak için).
"""
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout,
)

from common import style

MAX_ATTEMPTS = 5
LOCK_SECONDS = 30


class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.dealer = None
        self._failed_attempts = 0
        self.setWindowTitle("GivorPartners — Bayi Girişi")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(14)

        logo = QLabel("◈ GivorPartners", objectName="logoText")
        logo.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Bayi hesabınızla giriş yapın",
                          objectName="subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        form = QFormLayout()
        form.setSpacing(12)
        self.username = QLineEdit()
        self.username.setPlaceholderText("Kullanıcı adı")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Şifre")
        self.password.returnPressed.connect(self._try_login)
        form.addRow("Kullanıcı Adı:", self.username)
        form.addRow("Şifre:", self.password)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet(
            f"color: {style.palette()['red']}; font-size: 12px;")
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        cancel_button = QPushButton("Vazgeç")
        cancel_button.clicked.connect(self.reject)
        self.login_button = QPushButton("Giriş Yap", objectName="primary")
        self.login_button.setMinimumHeight(42)
        self.login_button.clicked.connect(self._try_login)
        buttons.addWidget(cancel_button)
        buttons.addWidget(self.login_button, 1)
        layout.addLayout(buttons)

        self.username.setFocus()

    def _lock(self):
        """Kaba kuvvete karşı girişi geçici olarak kilitler."""
        for widget in (self.username, self.password, self.login_button):
            widget.setEnabled(False)
        self.error_label.setText(
            f"Çok fazla başarısız deneme — {LOCK_SECONDS} sn bekleyin.")
        QTimer.singleShot(LOCK_SECONDS * 1000, self._unlock)

    def _unlock(self):
        self._failed_attempts = 0
        for widget in (self.username, self.password, self.login_button):
            widget.setEnabled(True)
        self.error_label.setText("")
        self.password.setFocus()

    def _try_login(self):
        if not self.login_button.isEnabled():
            return
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            self.error_label.setText("Kullanıcı adı ve şifre girin.")
            return
        dealer = self.db.verify_dealer_login(username, password)
        if not dealer:
            self._failed_attempts += 1
            self.password.clear()
            if self._failed_attempts >= MAX_ATTEMPTS:
                self._lock()
            else:
                remaining = MAX_ATTEMPTS - self._failed_attempts
                self.error_label.setText(
                    f"Kullanıcı adı veya şifre hatalı "
                    f"({remaining} deneme hakkı kaldı).")
                self.password.setFocus()
            return
        self.dealer = dealer
        self.accept()
