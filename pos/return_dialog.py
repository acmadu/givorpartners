"""Satış iade talebi dialogu."""
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout,
)
from pymongo.errors import PyMongoError


class ReturnDialog(QDialog):
    """Satış iade talebini oluşturma dialogu."""

    def __init__(self, parent, db, dealer: dict, cart: dict):
        super().__init__(parent)
        self.db = db
        self.dealer = dealer
        self.cart = cart
        self.setWindowTitle("Satış İade Talebi")
        self.setMinimumSize(600, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Başlık
        title = QLabel(f"🔄 {dealer['name']} — Satış İade", objectName="title")
        layout.addWidget(title)

        # Döndürülecek ürünler (sepetteki ürünlerden seçim)
        layout.addWidget(QLabel("Döndürülecek Ürünler:"))
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün Adı", "Sepet Adet", "İade Adet"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # İade nedenini seç
        form = QFormLayout()
        self.reason = QTextEdit()
        self.reason.setMaximumHeight(80)
        self.reason.setPlaceholderText(
            "Örn: Ürün hasarlı, istenenle uyuşmuyor, son kullanma tarihi geçti, vb.")
        form.addRow("İade Nedeni:", self.reason)
        layout.addLayout(form)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("İade Talebi Gönder")
        buttons.button(QDialogButtonBox.Cancel).setText("Vazgeç")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_cart_items()

    def _load_cart_items(self):
        """Sepetteki ürünleri tablodan seçilecek şekilde yükle."""
        for barcode, item in self.cart.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            cells = [
                barcode,
                item.get("name", ""),
                str(item.get("quantity", 0)),
                "0",  # İade adet (düzenlenebilir)
            ]
            for col, text in enumerate(cells):
                table_item = QTableWidgetItem(text)
                if col == 3:  # İade adet sütunu düzenlenebilir
                    table_item.setFlags(table_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, col, table_item)

    def _validate_and_accept(self):
        """İade talebini doğrula ve gönder."""
        items = []
        for row in range(self.table.rowCount()):
            return_qty_item = self.table.item(row, 3)
            return_qty = int(return_qty_item.text() or 0)
            if return_qty > 0:
                barcode = self.table.item(row, 0).text()
                name = self.table.item(row, 1).text()
                cart_qty = int(self.table.item(row, 2).text() or 0)
                if return_qty > cart_qty:
                    QMessageBox.warning(
                        self, "Hata",
                        f"{name}: İade adet, sepet adedini ({cart_qty}) aşamaz.")
                    return
                items.append({
                    "barcode": barcode,
                    "name": name,
                    "quantity": return_qty,
                    "reason": self.reason.toPlainText() or "Belirtilmemiş",
                })

        if not items:
            QMessageBox.warning(
                self, "Boş İade", "Lütfen en az bir ürün seçin.")
            return

        self.return_data = {
            "dealer_code": self.dealer["code"],
            "dealer_name": self.dealer["name"],
            "items": items,
            "created_at": datetime.now(),
            "status": "pending",
            "type": "customer_return",  # Müşteri iadesi
        }
        self.accept()
