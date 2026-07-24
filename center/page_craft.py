"""Ürün birleştirme (craft) sayfası.

Mevcut ürünlerden bileşen seçilir, adetleri belirlenir ve bunlardan
yeni bir ürün (paket/set) oluşturulur. Örnek: 1 kahve + 1 kupa =
"Kahve Hediye Seti". Yeni ürünün fiyatı bileşen toplamından önerilir,
istenirse değiştirilebilir; üretim adedi kadar bileşen stoğu düşülebilir.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)
from pymongo.errors import DuplicateKeyError, PyMongoError


def _money(value: float) -> str:
    return f"{value:.2f} ₺"


class CraftPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._products = []   # soldaki arama sonuçları
        self._recipe = {}     # barcode -> {barcode, name, price, quantity}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # ---------------- Sol: bileşen seçimi ----------------
        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(QLabel("Ürün Birleştir", objectName="title"))
        left.addWidget(QLabel("1. Bileşen ürünleri seçin",
                              objectName="subtitle"))

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Ürün ara (ad veya barkod)…")
        self.search.textChanged.connect(self._refresh_products)
        left.addWidget(self.search)

        self.product_table = QTableWidget(0, 4)
        self.product_table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün", "Fiyat", "Stok"])
        self.product_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.product_table.doubleClicked.connect(self._add_component)
        left.addWidget(self.product_table, 1)

        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Adet:"))
        self.component_quantity = QSpinBox(minimum=1, maximum=1000)
        add_row.addWidget(self.component_quantity)
        add_button = QPushButton("➜  Reçeteye Ekle", objectName="primary")
        add_button.clicked.connect(self._add_component)
        add_row.addWidget(add_button, 1)
        left.addLayout(add_row)
        layout.addLayout(left, 1)

        # ---------------- Sağ: reçete + yeni ürün ----------------
        right_card = QWidget(objectName="card")
        right = QVBoxLayout(right_card)
        right.setContentsMargins(24, 20, 24, 20)
        right.setSpacing(10)

        right.addWidget(QLabel("2. REÇETE — YENİ ÜRÜNÜN İÇERİĞİ",
                               objectName="cardTitle"))
        self.recipe_table = QTableWidget(0, 4)
        self.recipe_table.setHorizontalHeaderLabels(
            ["Ürün", "Adet", "Birim", "Tutar"])
        self.recipe_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.recipe_table.verticalHeader().setVisible(False)
        self.recipe_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recipe_table.setAlternatingRowColors(True)
        self.recipe_table.setSelectionBehavior(QTableWidget.SelectRows)
        right.addWidget(self.recipe_table, 1)

        recipe_buttons = QHBoxLayout()
        remove_button = QPushButton("🗑 Bileşeni Çıkar")
        remove_button.clicked.connect(self._remove_component)
        clear_button = QPushButton("Temizle")
        clear_button.clicked.connect(self._clear_recipe)
        self.sum_label = QLabel("Bileşen toplamı: 0,00 ₺",
                                objectName="subtitle")
        recipe_buttons.addWidget(remove_button)
        recipe_buttons.addWidget(clear_button)
        recipe_buttons.addStretch()
        recipe_buttons.addWidget(self.sum_label)
        right.addLayout(recipe_buttons)

        right.addWidget(QLabel("3. YENİ ÜRÜN BİLGİLERİ",
                               objectName="cardTitle"))
        form = QFormLayout()
        form.setSpacing(8)
        self.new_barcode = QLineEdit()
        self.new_barcode.setPlaceholderText("Yeni ürünün barkodu (zorunlu)")
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("Yeni ürünün adı (zorunlu)")
        self.new_price = QDoubleSpinBox(maximum=1_000_000, decimals=2,
                                        suffix=" ₺")
        self.new_vat = QSpinBox(maximum=100, suffix=" %")
        self.new_vat.setValue(20)
        self.assemble_count = QSpinBox(minimum=1, maximum=100000)
        self.deduct_stock = QCheckBox(
            "Bileşen stoklarından düş (üretim adedi × reçete)")
        self.deduct_stock.setChecked(True)

        form.addRow("Barkod:", self.new_barcode)
        form.addRow("Ürün Adı:", self.new_name)
        form.addRow("Satış Fiyatı:", self.new_price)
        form.addRow("KDV:", self.new_vat)
        form.addRow("Üretim Adedi (stok):", self.assemble_count)
        form.addRow("", self.deduct_stock)
        right.addLayout(form)

        create_button = QPushButton("🧩  ÜRÜNÜ OLUŞTUR", objectName="success")
        create_button.setMinimumHeight(46)
        create_button.clicked.connect(self._create_product)
        right.addWidget(create_button)

        layout.addWidget(right_card, 1)

    # ------------------------------------------------------------ Liste
    def refresh(self):
        self._refresh_products()

    def _refresh_products(self):
        self._products = self.db.get_products(self.search.text().strip())
        self.product_table.setRowCount(len(self._products))
        for row, product in enumerate(self._products):
            cells = [
                product.get("barcode", ""),
                product.get("name", ""),
                _money(product.get("price", 0)),
                str(product.get("stock", 0)),
            ]
            for column, text in enumerate(cells):
                self.product_table.setItem(row, column,
                                           QTableWidgetItem(text))

    # ----------------------------------------------------------- Reçete
    def _add_component(self):
        row = self.product_table.currentRow()
        if not (0 <= row < len(self._products)):
            QMessageBox.information(self, "Seçim Yok",
                                    "Soldaki listeden bir ürün seçin.")
            return
        product = self._products[row]
        barcode = product["barcode"]
        quantity = self.component_quantity.value()
        if barcode in self._recipe:
            self._recipe[barcode]["quantity"] += quantity
        else:
            self._recipe[barcode] = {
                "barcode": barcode,
                "name": product.get("name", ""),
                "price": float(product.get("price", 0)),
                "quantity": quantity,
            }
        self.component_quantity.setValue(1)
        self._render_recipe()

    def _remove_component(self):
        row = self.recipe_table.currentRow()
        keys = list(self._recipe)
        if 0 <= row < len(keys):
            del self._recipe[keys[row]]
            self._render_recipe()

    def _clear_recipe(self):
        self._recipe.clear()
        self._render_recipe()

    def _recipe_total(self) -> float:
        return sum(c["price"] * c["quantity"]
                   for c in self._recipe.values())

    def _render_recipe(self):
        self.recipe_table.setRowCount(len(self._recipe))
        for row, component in enumerate(self._recipe.values()):
            cells = [
                component["name"],
                str(component["quantity"]),
                _money(component["price"]),
                _money(component["price"] * component["quantity"]),
            ]
            for column, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                if column >= 1:
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.recipe_table.setItem(row, column, cell)
        total = self._recipe_total()
        self.sum_label.setText(
            f"Bileşen toplamı: {_money(total)}")
        # Fiyat önerisi — kullanıcı isterse üzerine yazar
        self.new_price.setValue(total)

    # ------------------------------------------------------------ Üretim
    def _create_product(self):
        if not self._recipe:
            QMessageBox.warning(self, "Reçete Boş",
                                "Önce en az bir bileşen ekleyin.")
            return
        barcode = self.new_barcode.text().strip()
        name = self.new_name.text().strip()
        if not barcode or not name:
            QMessageBox.warning(self, "Eksik Bilgi",
                                "Yeni ürünün barkodu ve adı zorunludur.")
            return
        if barcode in self._recipe:
            QMessageBox.warning(self, "Geçersiz Barkod",
                                "Yeni ürünün barkodu bileşenlerden "
                                "farklı olmalıdır.")
            return

        count = self.assemble_count.value()
        components = [
            {"barcode": c["barcode"], "name": c["name"],
             "quantity": c["quantity"]}
            for c in self._recipe.values()
        ]

        # Stok yeterlilik kontrolü
        if self.deduct_stock.isChecked():
            shortages = []
            for component in components:
                current = self.db.products.find_one(
                    {"barcode": component["barcode"]}) or {}
                need = component["quantity"] * count
                have = int(current.get("stock", 0))
                if have < need:
                    shortages.append(
                        f"• {component['name']}: gerekli {need}, stok {have}")
            if shortages:
                answer = QMessageBox.question(
                    self, "Stok Yetersiz",
                    "Bazı bileşenlerin stoğu yetersiz:\n\n"
                    + "\n".join(shortages)
                    + "\n\nYine de devam edilsin mi? (Stoklar eksiye düşer)")
                if answer != QMessageBox.Yes:
                    return

        product = {
            "barcode": barcode,
            "name": name,
            "price": self.new_price.value(),
            "vat": self.new_vat.value(),
            "stock": count,
            "box_barcode": "",
            "box_quantity": 1,
            "components": components,  # reçete kaydı (bilgi amaçlı)
        }
        try:
            self.db.create_combined_product(
                product, components, count, self.deduct_stock.isChecked())
        except DuplicateKeyError:
            QMessageBox.warning(self, "Hata",
                                "Bu barkodla kayıtlı bir ürün zaten var.")
            return
        except PyMongoError as error:
            QMessageBox.critical(self, "Veritabanı Hatası",
                                 f"Ürün oluşturulamadı:\n{error}")
            return

        QMessageBox.information(
            self, "Ürün Oluşturuldu",
            f"'{name}' oluşturuldu — stok: {count}\n"
            f"İçerik: " + ", ".join(
                f"{c['quantity']}× {c['name']}" for c in components))
        self._clear_recipe()
        self.new_barcode.clear()
        self.new_name.clear()
        self.new_vat.setValue(20)
        self.assemble_count.setValue(1)
        self._refresh_products()
