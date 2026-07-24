"""Ürün yönetimi sayfası — listeleme, ekleme, düzenleme, silme.

Her ürünün tekil barkodu ve isteğe bağlı bir koli barkodu vardır.
Koli barkodu kasada okutulduğunda 'koli adedi' kadar ürün sepete eklenir.
"""
from datetime import date, datetime

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from pymongo.errors import DuplicateKeyError, PyMongoError

# Son kullanım tarihi yaklaşan ürünleri vurgula (gün cinsinden)
_WARNING_DAYS = 30


class ProductDialog(QDialog):
    def __init__(self, parent=None, product: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Ürün Düzenle" if product else "Yeni Ürün")
        self.setMinimumWidth(420)
        product = product or {}

        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        self.barcode = QLineEdit(product.get("barcode", ""))
        self.barcode.setPlaceholderText("Ürün barkodu (zorunlu)")
        self.name = QLineEdit(product.get("name", ""))
        self.name.setPlaceholderText("Ürün adı (zorunlu)")
        self.price = QDoubleSpinBox(maximum=1_000_000, decimals=2, suffix=" ₺")
        self.price.setValue(float(product.get("price", 0)))
        self.vat = QSpinBox(maximum=100, suffix=" %")
        self.vat.setValue(int(product.get("vat", 20)))
        self.stock = QSpinBox(minimum=-99999, maximum=1_000_000)
        self.stock.setValue(int(product.get("stock", 0)))
        self.box_barcode = QLineEdit(product.get("box_barcode", ""))
        self.box_barcode.setPlaceholderText("Koli barkodu (isteğe bağlı)")
        self.box_quantity = QSpinBox(minimum=1, maximum=10000)
        self.box_quantity.setValue(int(product.get("box_quantity", 1) or 1))
        self.unit = QComboBox()
        self.unit.addItems(["adet", "mL", "L", "gram", "kg", "cm", "m"])
        unit_value = product.get("unit", "adet")
        idx = self.unit.findText(unit_value)
        if idx >= 0:
            self.unit.setCurrentIndex(idx)
        
        # Tarihler (Ay/Yıl formatı: MM/YYYY)
        self.manufactured_date = QLineEdit()
        self.manufactured_date.setPlaceholderText("MM/YYYY (örn: 01/2025)")
        if product.get("manufactured_date"):
            mfg = product.get("manufactured_date")
            if isinstance(mfg, datetime):
                mfg = mfg.date()
            elif isinstance(mfg, str):
                mfg = date.fromisoformat(mfg)
            self.manufactured_date.setText(f"{mfg.month:02d}/{mfg.year}")
        
        self.expiry_date = QLineEdit()
        self.expiry_date.setPlaceholderText("MM/YYYY (örn: 06/2025)")
        if product.get("expiry_date"):
            exp = product.get("expiry_date")
            if isinstance(exp, datetime):
                exp = exp.date()
            elif isinstance(exp, str):
                exp = date.fromisoformat(exp)
            self.expiry_date.setText(f"{exp.month:02d}/{exp.year}")

        form.addRow("Barkod:", self.barcode)
        form.addRow("Ürün Adı:", self.name)
        form.addRow("Satış Fiyatı:", self.price)
        form.addRow("KDV:", self.vat)
        form.addRow("Stok:", self.stock)
        form.addRow("Birim:", self.unit)
        form.addRow("Üretim Tarihi:", self.manufactured_date)
        form.addRow("Son Kullanım Tarihi:", self.expiry_date)
        form.addRow("Koli Barkodu:", self.box_barcode)
        form.addRow("Koli İçi Adet:", self.box_quantity)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Kaydet")
        buttons.button(QDialogButtonBox.Cancel).setText("Vazgeç")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validate(self):
        if not self.barcode.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi",
                                "Barkod ve ürün adı zorunludur.")
            return
        self.accept()

    def product_data(self) -> dict:
        # Tarih parse et (MM/YYYY → ayın ilk günü olarak datetime)
        def parse_month_year(text: str) -> datetime:
            text = text.strip()
            if not text or "/" not in text:
                return datetime.now()
            try:
                month, year = text.split("/")
                return datetime(int(year), int(month), 1, 0, 0, 0)
            except:
                return datetime.now()
        
        return {
            "barcode": self.barcode.text().strip(),
            "name": self.name.text().strip(),
            "price": self.price.value(),
            "vat": self.vat.value(),
            "stock": self.stock.value(),
            "unit": self.unit.currentText(),
            "manufactured_date": parse_month_year(self.manufactured_date.text()),
            "expiry_date": parse_month_year(self.expiry_date.text()),
            "box_barcode": self.box_barcode.text().strip(),
            "box_quantity": self.box_quantity.value(),
        }


class ProductsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top = QHBoxLayout()
        title = QLabel("Ürünler", objectName="title")
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Ürün adı veya barkod ara…")
        self.search.setFixedWidth(320)
        self.search.textChanged.connect(self.refresh)
        add_button = QPushButton("＋ Yeni Ürün", objectName="primary")
        add_button.clicked.connect(self._add_product)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.search)
        top.addWidget(add_button)
        layout.addLayout(top)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün Adı", "Fiyat", "KDV", "Birim", "Stok", 
             "Üretim", "SKT", "Koli Barkodu", "Koli Adet", "Durum"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._edit_product)
        layout.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        info = QLabel("Düzenlemek için satıra çift tıklayın.",
                      objectName="subtitle")
        edit_button = QPushButton("✏ Düzenle")
        edit_button.clicked.connect(self._edit_product)
        delete_button = QPushButton("🗑 Sil", objectName="danger")
        delete_button.clicked.connect(self._delete_product)
        bottom.addWidget(info)
        bottom.addStretch()
        bottom.addWidget(edit_button)
        bottom.addWidget(delete_button)
        layout.addLayout(bottom)

    def refresh(self):
        from common import style
        today = date.today()
        products = self.db.get_products(self.search.text().strip())
        self.table.setRowCount(len(products))
        pal = style.palette()
        for row, product in enumerate(products):
            expiry = product.get("expiry_date")
            if isinstance(expiry, datetime):
                expiry = expiry.date()
            if expiry:
                days_left = (expiry - today).days
                expiry_text = expiry.strftime("%m/%Y")  # Ay/Yıl formatı
                if days_left < 0:
                    expiry_color = pal["red"]
                elif days_left <= _WARNING_DAYS:
                    expiry_color = pal["yellow"]
                else:
                    expiry_color = pal["green"]
            else:
                expiry_text = "—"
                expiry_color = None
            
            # Üretim tarihi
            manufactured = product.get("manufactured_date")
            if isinstance(manufactured, datetime):
                manufactured = manufactured.date()
            mfg_text = manufactured.strftime("%m/%Y") if manufactured else "—"  # Ay/Yıl formatı

            cells = [
                product.get("barcode", ""),
                product.get("name", ""),
                f"{product.get('price', 0):.2f} ₺",
                f"%{product.get('vat', 0)}",
                product.get("unit", "adet"),
                str(product.get("stock", 0)),
                mfg_text,
                expiry_text,
                product.get("box_barcode", "") or "—",
                str(product.get("box_quantity", "—")),
                "✓" if expiry and (expiry - today).days > 0 else "⚠" if expiry else "—",
            ]
            for column, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if column == 7 and expiry_color:  # SKT sütunu
                    item.setForeground(QColor(expiry_color))
                if column == 10 and expiry_color:  # Durum sütunu
                    item.setForeground(QColor(expiry_color))
                self.table.setItem(row, column, item)

    def _selected_barcode(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        return self.table.item(row, 0).text()

    def _add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                self.db.add_product(dialog.product_data())
            except DuplicateKeyError:
                QMessageBox.warning(self, "Hata", "Bu barkod zaten kayıtlı.")
            except PyMongoError as error:
                QMessageBox.critical(self, "Veritabanı Hatası",
                                     f"Ürün kaydedilemedi:\n{error}")
            self.refresh()

    def _edit_product(self):
        barcode = self._selected_barcode()
        if not barcode:
            QMessageBox.information(self, "Seçim Yok", "Lütfen bir ürün seçin.")
            return
        product = self.db.products.find_one({"barcode": barcode})
        dialog = ProductDialog(self, product)
        if dialog.exec_() == QDialog.Accepted:
            try:
                self.db.update_product(barcode, dialog.product_data())
            except DuplicateKeyError:
                QMessageBox.warning(self, "Hata",
                                    "Yeni barkod başka bir üründe kayıtlı.")
            except PyMongoError as error:
                QMessageBox.critical(self, "Veritabanı Hatası",
                                     f"Ürün güncellenemedi:\n{error}")
            self.refresh()

    def _delete_product(self):
        barcode = self._selected_barcode()
        if not barcode:
            QMessageBox.information(self, "Seçim Yok", "Lütfen bir ürün seçin.")
            return
        answer = QMessageBox.question(
            self, "Ürünü Sil", f"'{barcode}' barkodlu ürün silinsin mi?"
        )
        if answer == QMessageBox.Yes:
            self.db.delete_product(barcode)
            self.refresh()
