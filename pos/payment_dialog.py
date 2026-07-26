"""Kart ödeme ekranı — terminal bekleme ve sonuç gösterimi.

Akış:
  1. Kasiyer "KREDİ KARTI" butonuna basar → CardPaymentDialog açılır
  2. Manuel modda: tutar gösterilir, kasiyer terminalde ödemeyi başlatır,
     "Onaylandı" veya "Reddedildi" butonuna basar.
  3. Ingenico/Seri/TCP modunda: tutar terminale gönderilir, yanıt beklenir,
     sonuç otomatik gösterilir; kasiyer "İptal" ile istediği zaman çıkabilir.
  4. Onaylandıysa: dialog.result == PaymentResult(approved=True, ...)
     Reddedildiyse veya iptal edildiyse: dialog.result is None
"""
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from common import style
from pos.payment_terminal import PaymentResult, PaymentTerminal, TerminalMode


class _TerminalWorker(QThread):
    """Engellemeyen terminal iletişimi için arka plan iş parçacığı."""
    finished = pyqtSignal(object)  # PaymentResult

    def __init__(self, terminal: PaymentTerminal, amount: float):
        super().__init__()
        self.terminal = terminal
        self.amount = amount

    def run(self):
        result = self.terminal.request_payment(self.amount)
        self.finished.emit(result)


class CardPaymentDialog(QDialog):
    """Kart ödeme sürecini yöneten dialog."""

    def __init__(self, parent, terminal: PaymentTerminal, amount: float):
        super().__init__(parent)
        self.terminal = terminal
        self.amount = amount
        self.result: PaymentResult | None = None
        self._dots = 0

        self.setWindowTitle("Kart Ödemesi")
        self.setMinimumSize(500, 380)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 36, 48, 32)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("💳  KREDİ KARTI ÖDEMESİ", objectName="title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Tutar
        amount_text = (f"{amount:,.2f} ₺"
                       .replace(",", "X").replace(".", ",").replace("X", "."))
        amount_label = QLabel(amount_text, objectName="totalAmount")
        amount_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(amount_label)

        # Durum mesajı (Ingenico'da "●●●" animasyonu buraya)
        self.status_label = QLabel("", objectName="subtitle")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Onay / Ret butonları (manuel mod veya Ingenico hata)
        self.confirm_row = QHBoxLayout()
        self.confirm_button = QPushButton("✔  Onaylandı", objectName="success")
        self.confirm_button.setMinimumHeight(56)
        self.confirm_button.clicked.connect(self._manual_approve)
        self.decline_button = QPushButton("✖  Reddedildi", objectName="danger")
        self.decline_button.setMinimumHeight(56)
        self.decline_button.clicked.connect(self._manual_decline)
        self.confirm_row.addWidget(self.confirm_button)
        self.confirm_row.addWidget(self.decline_button)
        layout.addLayout(self.confirm_row)

        # İptal butonu
        self.cancel_button = QPushButton("↩  İptal — Sepete Dön")
        self.cancel_button.setMinimumHeight(42)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self._start_payment()

    def _start_payment(self):
        mode = self.terminal.mode
        if mode == TerminalMode.MANUAL:
            self.status_label.setText(
                "Tutarı terminale girin ve müşterinin\n"
                "kartını okutmasını bekleyin.\n\n"
                "İşlem tamamlandığında aşağıdan sonucu seçin.")
            return

        if mode == TerminalMode.SIMULATE:
            self.status_label.setText(
                "🧪  SİMÜLASYON MODU\n\n"
                "Gerçek POS bağlantısı yok.\n"
                "Test için aşağıdan sonucu seçin.")
            self.status_label.setStyleSheet(
                "color: #e67e22; font-weight: bold; font-size: 14px;")
            return

        # Ingenico / Seri / TCP — arka planda gönder
        mode_label = {
            TerminalMode.INGENICO: "Ingenico terminal",
            TerminalMode.SERIAL:   "Seri port terminal",
            TerminalMode.TCP:      "TCP terminal",
        }.get(mode, "Terminal")
        self._waiting_label = f"{mode_label} bekleniyor"
        self.status_label.setText(f"⏳  {self._waiting_label}…")
        self.confirm_button.hide()
        self.decline_button.hide()

        # Nokta animasyonu
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._animate_dots)
        self._dot_timer.start(600)

        self._worker = _TerminalWorker(self.terminal, self.amount)
        self._worker.finished.connect(self._on_terminal_response)
        self._worker.start()

    def _animate_dots(self):
        self._dots = (self._dots + 1) % 4
        self.status_label.setText(
            f"⏳  {self._waiting_label}{'.' * self._dots}"
            + "\n\nMüşteri kartını terminale okutmalıdır.")

    # ----------------------------------------------------------------- Handlers
    def _on_terminal_response(self, result: PaymentResult):
        self._dot_timer.stop()
        pal = style.palette()
        if result.approved:
            self._show_approved(result)
        else:
            self.status_label.setText(
                f"❌  {result.error_message or 'Terminal reddetti.'}")
            self.status_label.setStyleSheet(
                f"color: {pal['red']}; font-size: 15px;")
            # Kasiyere manuel onay seçeneği sun
            self.confirm_button.show()
            self.decline_button.show()

    def _show_approved(self, result: PaymentResult):
        pal = style.palette()
        self.result = result
        lines = ["✅  Ödeme onaylandı!"]
        if result.auth_code:
            lines.append(f"Onay Kodu: {result.auth_code}")
        if result.ref_no:
            lines.append(f"Referans No: {result.ref_no}")
        if result.card_last4:
            lines.append(f"Kart: ****{result.card_last4}")
        self.status_label.setText("\n".join(lines))
        self.status_label.setStyleSheet(
            f"color: {pal['green']}; font-size: 15px; font-weight: bold;")
        self.confirm_button.hide()
        self.decline_button.hide()
        self.cancel_button.setText("✔  Tamam — Satışı Tamamla")
        self.cancel_button.setObjectName("success")
        self.cancel_button.style().unpolish(self.cancel_button)
        self.cancel_button.style().polish(self.cancel_button)
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.accept)

    def _manual_approve(self):
        self.result = PaymentResult(approved=True, amount=self.amount, auth_code="", ref_no="")
        self.accept()

    def _manual_decline(self):
        self.result = None
        self.reject()

    def reject(self):
        if hasattr(self, "_dot_timer"):
            self._dot_timer.stop()
        if hasattr(self, "_worker") and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(1000)
        super().reject()

