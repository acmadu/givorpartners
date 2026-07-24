"""Merkez'den gönderilen stokları bayinin onaylaması."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox,
)
from pymongo.errors import PyMongoError


class PendingStockApprovalDialog(QDialog):
    """Merkez'den gelen beklemede stokları onaylama."""

    def __init__(self, parent, db, dealer_code: str, dealer_name: str):
        super().__init__(parent)
        self.db = db
        self.dealer_code = dealer_code
        self.dealer_name = dealer_name
        self.setWindowTitle("✓ Depo Onayları")
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        title = QLabel(f"Merkez'den Gelen Stoklar — {dealer_name}")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        # Tablo: Ürün | Beklemede | İşlem
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Ürün Adı", "Barkod", "Beklemede (adet)", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._on_table_clicked)

        self.refresh()
        layout.addWidget(self.table, 1)

        # Bilgi
        info = QLabel(
            "Merkez'den gelen stokları gösteriyor.\n"
            "Satırda 'Onayla' basarak deponuza ekleyebilirsiniz.",
            objectName="subtitle")
        layout.addWidget(info)

        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _on_table_clicked(self, row: int, col: int):
        """Onayla butonuna tıklandığında."""
        if col != 3:
            return
        item = self.table.item(row, 1)
        if not item:
            return
        barcode = item.text()
        self.approve_stock(barcode)

    def refresh(self):
        """Onay beklemede stokları göster."""
        self.table.setRowCount(0)

        try:
            # pending_quantity > 0 olan kayıtları bul
            pending_docs = list(self.db.dealer_stocks.find({
                "dealer_code": self.dealer_code,
                "pending_quantity": {"$gt": 0}
            }))

            for doc in pending_docs:
                barcode = doc['barcode']
                qty = doc.get('pending_quantity', 0)

                # Ürün detayları
                product = self.db.products.find_one({"barcode": barcode})
                if not product:
                    continue

                row = self.table.rowCount()
                self.table.insertRow(row)

                cells = [
                    product['name'],
                    barcode,
                    f"{qty} {product.get('unit', 'adet')}",
                    "✓ Onayla",
                ]

                for col, text in enumerate(cells):
                    item = QTableWidgetItem(text)
                    if col == 3:
                        item.setFlags(item.flags() | Qt.ItemIsEnabled)
                    self.table.setItem(row, col, item)

        except PyMongoError:
            pass

    def approve_stock(self, barcode: str):
        """Stokı onayla ve depoya ekle."""
        try:
            doc = self.db.dealer_stocks.find_one({
                "dealer_code": self.dealer_code,
                "barcode": barcode
            })

            if not doc:
                return

            pending_qty = doc.get('pending_quantity', 0)
            current_stock = doc.get('stock', 0)

            # pending'den stock'a aktar
            self.db.dealer_stocks.update_one(
                {"dealer_code": self.dealer_code, "barcode": barcode},
                {
                    "$inc": {"stock": pending_qty, "pending_quantity": -pending_qty},
                    "$set": {"status": "approved"}
                })

            product = self.db.products.find_one({"barcode": barcode})
            QMessageBox.information(
                self, "✓ Onaylandı",
                f"{pending_qty} {product.get('unit', 'adet')} "
                f"{product['name']}\n"
                f"Deponuza eklendi.")

            self.refresh()

        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Onaylanamadı:\n{error}")
