"""Sipariş iade talebi — merkezden alınan ürünleri geri gönderme."""
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
)
from pymongo.errors import PyMongoError


class OrderReturnDialog(QDialog):
    """Merkezden alınan sipariş ürünlerini iade etme dialogu."""

    def __init__(self, parent, db, dealer: dict):
        super().__init__(parent)
        self.db = db
        self.dealer = dealer
        self.setWindowTitle("Sipariş İadesi")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Başlık
        title = QLabel(f"📦 {dealer['name']} — Sipariş İadesi", 
                       objectName="title")
        layout.addWidget(title)

        # Sipariş seçimi
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Sipariş Seçin:"))
        self.order_combo = QHBoxLayout()  # Placeholder
        layout.addLayout(top_row)

        # İade edilecek ürünler tablosu
        layout.addWidget(QLabel("İade Edilecek Ürünler:"))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün Adı", "Sipariş Adet", "İade Adet", "Nedeni"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # İade notları
        layout.addWidget(QLabel("Genel Not (isteğe bağlı):"))
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Örn: Ürün hasarlı, eksik gelmişti, vb.")
        layout.addWidget(self.notes)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("✓ İade Talebini Gönder")
        buttons.button(QDialogButtonBox.Cancel).setText("✕ Vazgeç")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_confirmed_orders()

    def _load_confirmed_orders(self):
        """Onaylanan siparişleri yükle."""
        try:
            orders = self.db.get_orders(
                dealer_code=self.dealer.get("code", ""),
                status="confirmed"
            )
            if not orders:
                QMessageBox.information(
                    self, "Sipariş Yok",
                    "Onaylanan siparişiniz bulunmamaktadır.")
                self.reject()
                return
            
            # Eğer sadece 1 sipariş varsa onu seç
            self._load_order_items(orders[0])
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Siparişler yüklenemedi:\n{error}")
            self.reject()

    def _load_order_items(self, order: dict):
        """Seçili siparişin ürünlerini tabloya yükle."""
        self.current_order = order
        self.table.setRowCount(0)

        for item in order.get("items", []):
            row = self.table.rowCount()
            self.table.insertRow(row)

            barcode_item = QTableWidgetItem(item.get("barcode", ""))
            barcode_item.setFlags(barcode_item.flags() & ~Qt.ItemIsEditable)

            name_item = QTableWidgetItem(item.get("name", ""))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)

            qty_item = QTableWidgetItem(str(item.get("quantity_boxes", 0)))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)

            return_qty_item = QTableWidgetItem("0")
            return_qty_item.setFlags(return_qty_item.flags() | Qt.ItemIsEditable)

            reason_item = QTableWidgetItem("")
            reason_item.setFlags(reason_item.flags() | Qt.ItemIsEditable)

            self.table.setItem(row, 0, barcode_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, qty_item)
            self.table.setItem(row, 3, return_qty_item)
            self.table.setItem(row, 4, reason_item)

    def _validate_and_accept(self):
        """İade talebini doğrula ve gönder."""
        items = []
        
        for row in range(self.table.rowCount()):
            return_qty_text = self.table.item(row, 3).text()
            return_qty = int(return_qty_text or 0)
            
            if return_qty <= 0:
                continue
            
            barcode = self.table.item(row, 0).text()
            name = self.table.item(row, 1).text()
            ordered_qty = int(self.table.item(row, 2).text() or 0)
            reason = self.table.item(row, 4).text() or "Belirtilmemiş"
            
            if return_qty > ordered_qty:
                QMessageBox.warning(
                    self, "Hata",
                    f"{name}: İade adet, sipariş adedini ({ordered_qty}) aşamaz.")
                return
            
            items.append({
                "barcode": barcode,
                "name": name,
                "quantity": return_qty,
                "reason": reason,
            })

        if not items:
            QMessageBox.warning(self, "Hata", "Lütfen en az bir ürün seçin.")
            return

        self.return_data = {
            "order_id": str(self.current_order.get("_id", "")),
            "dealer_code": self.dealer.get("code", ""),
            "dealer_name": self.dealer.get("name", ""),
            "items": items,
            "notes": self.notes.toPlainText(),
            "created_at": datetime.now(),
            "status": "pending",  # pending/approved/rejected
            "type": "order_return",  # Müşteri iadesiyle ayırt etmek için
        }
        self.accept()
