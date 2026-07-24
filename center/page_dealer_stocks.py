"""Merkez'de tüm bayilerin stoklarını yönetme sayfası.

Merkez:
- Tüm bayilerin stok durumunu görür
- Bayilere ürün dağıtabilir (transfer)
- Her bayi için kaç ürün olduğunu takip eder
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QComboBox,
)
from pymongo.errors import PyMongoError


class StockTransferDialog(QDialog):
    """Bayiye ürün dağıtma diyaloğu."""

    def __init__(self, parent, db, product: dict):
        super().__init__(parent)
        self.db = db
        self.product = product
        self.setWindowTitle(f"Ürün Dağıt: {product['name']}")
        self.setMinimumWidth(400)

        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        # Ürün bilgisi
        form.addRow("Ürün:", QLabel(product['name']))
        form.addRow("Barkod:", QLabel(product['barcode']))
        current_stock = product.get('stock', 0)
        form.addRow("Merkez Stoğu:", QLabel(f"{current_stock} {product.get('unit', 'adet')}"))

        # Bayi seçimi
        self.dealer_combo = QComboBox()
        try:
            dealers = self.db.dealers.find({})
            self.dealers_list = list(dealers)
            for dealer in self.dealers_list:
                self.dealer_combo.addItem(dealer['name'], dealer['code'])
        except PyMongoError:
            pass
        form.addRow("Bayi:", self.dealer_combo)

        # Miktar
        self.quantity = QSpinBox(minimum=1, maximum=current_stock)
        self.quantity.setValue(1)
        form.addRow("Dağıtılacak Miktar:", self.quantity)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Dağıt")
        buttons.button(QDialogButtonBox.Cancel).setText("Vazgeç")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validate(self):
        if not self.dealer_combo.currentData():
            QMessageBox.warning(self, "Hata", "Bayi seçin.")
            return
        self.accept()

    def transfer_data(self) -> dict:
        return {
            "dealer_code": self.dealer_combo.currentData(),
            "dealer_name": self.dealer_combo.currentText(),
            "quantity": self.quantity.value(),
        }


class DealerStocksPage(QWidget):
    """Merkez'den tüm bayilerin stoklarını yönetme."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top = QHBoxLayout()
        title = QLabel("Bayi Stokları", objectName="title")
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Bayi veya ürün ara…")
        self.search.setFixedWidth(320)
        self.search.textChanged.connect(self.refresh)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.search)
        layout.addLayout(top)

        # Tablo: Bayi | Ürün | Barkod | Stok | İşlem
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Bayi", "Ürün Adı", "Barkod", "Stok", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

        # Merkez stoğu gösterimi
        info = QLabel(
            "Merkez'deki ürünler → Bayilere dağıt\n"
            "Satırda 'Dağıt' butonuna tıklayarak ürünü bayiye aktarabilirsiniz.",
            objectName="subtitle")
        layout.addWidget(info)

        self.refresh()

    def refresh(self):
        """Tüm bayi stoklarını göster."""
        self.table.setRowCount(0)
        search_text = self.search.text().strip().lower()

        try:
            dealers = list(self.db.dealers.find({}))
            if not dealers:
                return

            # Merkez stoğundaki ürünler
            products = list(self.db.get_products(search_text) if search_text else self.db.products.find({}))

            row = 0
            for dealer in dealers:
                dealer_code = dealer['code']
                dealer_name = dealer['name']

                # Bu bayinin stok kayıtlarını al
                dealer_stock_docs = list(self.db.dealer_stocks.find(
                    {"dealer_code": dealer_code}))
                # stock ve pending_quantity'i birleştir
                dealer_stock_map = {doc['barcode']: doc.get('stock', 0) + doc.get('pending_quantity', 0)
                                    for doc in dealer_stock_docs}

                # Ürünleri listele
                for product in products:
                    barcode = product['barcode']
                    name = product['name']
                    stocked = dealer_stock_map.get(barcode, 0)

                    # Satır ekle
                    self.table.insertRow(row)

                    cells = [
                        dealer_name,
                        name,
                        barcode,
                        f"{stocked} {product.get('unit', 'adet')}",
                        "📤 Dağıt",
                    ]

                    for col, text in enumerate(cells):
                        item = QTableWidgetItem(text)
                        if col == 4:  # İşlem sütunu tıklanabilir yap
                            item.setFlags(item.flags() | Qt.ItemIsEnabled)
                        self.table.setItem(row, col, item)

                    # Tag olarak dealer_code ve barcode kaydet
                    self.table.item(row, 0).setData(Qt.UserRole, (dealer_code, barcode))
                    row += 1

            # İşlem sütununa tıklama
            self.table.cellDoubleClicked.connect(self._on_cell_clicked)

        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Yüklenemedi:\n{error}")

    def _on_cell_clicked(self, row: int, col: int):
        """İşlem sütununa tıklandığında dağıt diyaloğu aç."""
        if col != 4:
            return

        barcode = self.table.item(row, 2).text()
        try:
            product = self.db.products.find_one({"barcode": barcode})
            if not product:
                QMessageBox.warning(self, "Hata", "Ürün bulunamadı.")
                return

            dialog = StockTransferDialog(self, self.db, product)
            if dialog.exec_() == QDialog.Accepted:
                transfer = dialog.transfer_data()
                self._execute_transfer(product, transfer)
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Hata:\n{error}")

    def _execute_transfer(self, product: dict, transfer: dict):
        """Ürünü merkez'den bayiye aktar (onay beklemede)."""
        barcode = product['barcode']
        qty = transfer['quantity']
        dealer_code = transfer['dealer_code']

        try:
            # Merkez stok azalt
            self.db.products.update_one(
                {"barcode": barcode},
                {"$inc": {"stock": -qty}})

            # Bayi'de pending stok arttır (onay beklemededir)
            self.db.dealer_stocks.update_one(
                {"dealer_code": dealer_code, "barcode": barcode},
                {
                    "$inc": {"pending_quantity": qty},
                    "$set": {"status": "pending"}
                },
                upsert=True)

            QMessageBox.information(
                self, "✓ Gönderildi (Onay Beklemede)",
                f"{qty} {product.get('unit', 'adet')} "
                f"{product['name']}\n"
                f"{transfer['dealer_name']}'e gönderildi.\n"
                f"Bayi onay yapmalıdır.")
            self.refresh()
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Dağıtılamadı:\n{error}")
