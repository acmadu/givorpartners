"""Bayi siparişi oluşturma dialogu — ürün seçme, koli adedi, dekont yükleme."""
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QComboBox, QSpinBox,
)
from pymongo.errors import PyMongoError


class OrderDialog(QDialog):
    """Koli bazlı sipariş oluşturma: ürün seçme, koli adedi, dekont, toplam."""

    def __init__(self, parent, db, dealer: dict):
        super().__init__(parent)
        self.db = db
        self.dealer = dealer
        self.dekont_file = None  # Yüklenen dekont dosyası
        self.setWindowTitle("Ürün Sipariş Et")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Başlık
        title = QLabel(f"🏬 {dealer['name']} — Ürün Sipariş Oluştur", 
                       objectName="title")
        layout.addWidget(title)

        # Siparişe eklenecek ürünler tablosu
        layout.addWidget(QLabel("Siparişe Eklenecek Ürünler (Sadece Koliyle):"))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün Adı", "Birim Fiyat ₺", "Koli Adet (Min: 1)", "Toplam ₺"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self._update_total)
        layout.addWidget(self.table, 2)

        # Ürün ekleme alanı
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Ürün ekle:"))
        self.product_combo = QComboBox()
        self.product_combo.addItem("— Seçin —", None)
        add_row.addWidget(self.product_combo, 1)
        add_button = QPushButton("➕ Tabloya Ekle")
        add_button.clicked.connect(self._add_product_to_table)
        add_row.addWidget(add_button)
        self._load_products_combo()
        layout.addLayout(add_row)

        # Dekont dosyası yükleme
        dekont_row = QHBoxLayout()
        dekont_row.addWidget(QLabel("📄 Dekont Dosyası:"))
        self.dekont_label = QLabel("Yüklenmedi", objectName="muted")
        dekont_row.addWidget(self.dekont_label, 1)
        dekont_button = QPushButton("📂 Dosya Seç")
        dekont_button.clicked.connect(self._select_dekont)
        dekont_row.addWidget(dekont_button)
        layout.addLayout(dekont_row)

        # Sipariş notları
        layout.addWidget(QLabel("Sipariş Notları (isteğe bağlı):"))
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addWidget(self.notes)

        # Toplam tutar
        total_row = QHBoxLayout()
        total_row.addStretch()
        total_row.addWidget(QLabel("Toplam:", objectName="cardTitle"))
        self.total_label = QLabel("0,00 ₺", objectName="totalAmount")
        self.total_label.setMinimumWidth(100)
        total_row.addWidget(self.total_label)
        layout.addLayout(total_row)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("✓ Sipariş Gönder")
        buttons.button(QDialogButtonBox.Cancel).setText("✕ Vazgeç")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_products_combo(self):
        """Ürünleri combo box'a yükle."""
        try:
            products = self.db.get_products("")
            for product in products:
                display = f"{product.get('name', '')} ({product.get('barcode', '')})"
                self.product_combo.addItem(display, product)
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Ürünler yüklenemedi:\n{error}")

    def _add_product_to_table(self):
        """Seçili ürünü tabloya ekle."""
        product = self.product_combo.currentData()
        if not product:
            QMessageBox.information(self, "Seçim Yok", "Lütfen bir ürün seçin.")
            return

        # Aynı ürün zaten tablodaysa miktarını artır
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == product.get("barcode"):
                qty_item = self.table.item(row, 3)
                if qty_item:
                    qty = int(qty_item.text() or 0) + 1
                    qty_item.setText(str(qty))
                self._update_total()
                return

        # Yeni satır ekle
        row = self.table.rowCount()
        self.table.insertRow(row)

        barcode_item = QTableWidgetItem(product.get("barcode", ""))
        barcode_item.setFlags(barcode_item.flags() & ~Qt.ItemIsEditable)
        name_item = QTableWidgetItem(product.get("name", ""))
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        price_item = QTableWidgetItem(f"{product.get('price', 0):.2f}")
        price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
        qty_item = QTableWidgetItem("1")
        total_item = QTableWidgetItem(f"{product.get('price', 0):.2f}")
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)

        self.table.setItem(row, 0, barcode_item)
        self.table.setItem(row, 1, name_item)
        self.table.setItem(row, 2, price_item)
        self.table.setItem(row, 3, qty_item)
        self.table.setItem(row, 4, total_item)

        self._update_total()

    def _update_total(self):
        """Toplam tutar ve satır toplamlarını güncelle. Koli adetini minimum 1'e kısıtla."""
        self.table.blockSignals(True)
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                price_item = self.table.item(row, 2)
                qty_item = self.table.item(row, 3)
                total_item = self.table.item(row, 4)
                if not price_item or not qty_item or not total_item:
                    continue
                price = float(price_item.text() or 0)
                qty_text = qty_item.text().strip()
                
                # Koli adetini sadece tam sayı ve minimum 1 yap
                try:
                    qty = int(qty_text)
                    if qty < 1:
                        qty = 1
                        qty_item.setText("1")
                except ValueError:
                    qty = 1
                    qty_item.setText("1")
                
                line_total = price * qty
                total_item.setText(f"{line_total:.2f}")
                total += line_total
            except (ValueError, AttributeError):
                pass
        self.table.blockSignals(False)
        self.total_label.setText(f"{total:.2f} ₺")

    def _select_dekont(self):
        """Dekont dosyası seç (PDF, JPG, PNG)."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Dekont Dosyası Seç", "",
            "Belgeler (*.pdf *.jpg *.jpeg *.png);;Tümü (*)"
        )
        if path:
            self.dekont_file = path
            filename = Path(path).name
            self.dekont_label.setText(f"✓ {filename}")

    def _validate_and_accept(self):
        """Siparişi doğrula ve gönder. Sadece koli bazlı sipariş (minimum 1)."""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Boş Sipariş",
                                "Lütfen en az bir ürün ekleyin.")
            return

        items = []
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                barcode = self.table.item(row, 0).text()
                name = self.table.item(row, 1).text()
                price = float(self.table.item(row, 2).text() or 0)
                qty_text = self.table.item(row, 3).text().strip()
                
                # Koli adetini tam sayı ve minimum 1 olacak şekilde dönüştür
                try:
                    qty = int(qty_text)
                except ValueError:
                    QMessageBox.warning(self, "Hata", 
                                      f"Satır {row + 1}: Koli adet tam sayı olmalı!")
                    return
                
                if qty < 1:
                    QMessageBox.warning(self, "Geçersiz Koli Adet",
                                      f"Satır {row + 1}: Koli adet en az 1 olmalı!")
                    return

                items.append({
                    "barcode": barcode,
                    "name": name,
                    "quantity_boxes": int(qty),
                    "unit_price": price,
                })
                total += price * qty
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "Geçersiz Veri",
                    f"Satır {row + 1} geçersiz veri içeriyor.")
                return

        if not items:
            QMessageBox.warning(self, "Boş Sipariş",
                                "Lütfen en az bir ürün adedi girin.")
            return

        self.order_data = {
            "dealer_code": self.dealer.get("code", ""),
            "dealer_name": self.dealer.get("name", ""),
            "items": items,
            "total": round(total, 2),
            "dekont_file": self.dekont_file,  # Path veya None
            "notes": self.notes.toPlainText(),
            "created_at": datetime.now(),
            "status": "pending",
        }
        self.accept()
