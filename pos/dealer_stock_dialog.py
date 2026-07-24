"""Bayinin depo/stok kontrolü diyaloğu."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout,
)
from pymongo.errors import PyMongoError


class DealerStockDialog(QDialog):
    """Bayinin tüm stok kayıtlarını gösterir."""

    def __init__(self, parent, db, dealer_code: str, dealer_name: str):
        super().__init__(parent)
        self.db = db
        self.dealer_code = dealer_code
        self.setWindowTitle(f"📦 {dealer_name} - Depo Stoğu")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün Adı", "Stok", "Kutu"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._load_stocks()

    def _load_stocks(self):
        """Bayi stoklarını tablo'ya yükle."""
        try:
            stocks = self.db.get_all_dealer_stocks(self.dealer_code)
            self.table.setRowCount(len(stocks))

            for row, stock_doc in enumerate(stocks):
                barcode = stock_doc.get("barcode", "")
                name = stock_doc.get("name", "?")
                qty = stock_doc.get("stock", 0)
                box_qty = stock_doc.get("box_quantity", 0)

                cells = [barcode, name, str(qty), str(box_qty)]
                for col, text in enumerate(cells):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    # Düşük stok uyarısı (50'den az)
                    if col == 2 and qty < 50:
                        item.setForeground(QColor("#dc3545"))  # Kırmızı
                    self.table.setItem(row, col, item)

        except PyMongoError as error:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"Stok yüklenemedi:\n{error}")
