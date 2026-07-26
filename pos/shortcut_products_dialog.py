"""Hızlı erişim kısayol ürünleri yönetimi."""
import logging
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QSpinBox,
    QMessageBox, QComboBox, QHeaderView
)
from PyQt5.QtGui import QFont
from pymongo.errors import PyMongoError
from common import style

logger = logging.getLogger(__name__)


class ShortcutProductDialog(QDialog):
    """Kısayol ürünleri yönetimi."""

    def __init__(self, db, dealer_code: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.dealer_code = dealer_code
        self.setWindowTitle("⭐ Kısayol Ürünleri Yönet")
        self.resize(700, 500)
        self._build_ui()
        self._load_shortcuts()

    def _build_ui(self):
        """Arayüz oluştur."""
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("⭐ Hızlı Erişim Kısayolları")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Açıklama
        info = QLabel(
            "POS panelinde hızlı erişim için ürünler ekle/kaldır.\n"
            "Seçili ürünler ana panel'de gösterilecek."
        )
        info.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 10px;")
        layout.addWidget(info)

        # Tablo: Mevcut kısayollar
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(4)
        self.shortcuts_table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün Adı", "Sıra", "Sil"]
        )
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.shortcuts_table.setMaximumHeight(250)
        layout.addWidget(QLabel("Mevcut Kısayollar:"))
        layout.addWidget(self.shortcuts_table)

        # Ürün ekleme
        add_section = QVBoxLayout()
        add_section.addWidget(QLabel("Yeni Ürün Ekle:"))

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Barkod:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barkod yazıp Enter'a basın...")
        self.barcode_input.returnPressed.connect(self._add_shortcut)
        add_layout.addWidget(self.barcode_input)

        add_btn = QPushButton("➕ Ekle")
        add_btn.clicked.connect(self._add_shortcut)
        add_layout.addWidget(add_btn)

        add_section.addLayout(add_layout)
        layout.addLayout(add_section)

        # Alt butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("✓ Tamam")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("✖ İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_shortcuts(self):
        """Kısayolları yükle."""
        try:
            dealer = self.db.dealers.find_one({"code": self.dealer_code})
            shortcuts = dealer.get("shortcut_products", []) if dealer else []

            self.shortcuts_table.setRowCount(len(shortcuts))

            for row, shortcut in enumerate(shortcuts):
                barcode = shortcut.get("barcode", "")
                
                # Ürün bilgilerini getir
                product = self.db["products"].find_one({"barcode": barcode})
                product_name = product.get("name", "?") if product else "❌ Silinmiş"

                # Barkod
                self.shortcuts_table.setItem(row, 0, QTableWidgetItem(barcode))

                # Ürün adı
                name_item = QTableWidgetItem(product_name)
                if not product:
                    name_item.setForeground(style.palette()["red"])
                self.shortcuts_table.setItem(row, 1, name_item)

                # Sıra (order)
                order_spinbox = QSpinBox()
                order_spinbox.setValue(shortcut.get("order", row + 1))
                order_spinbox.setMinimum(1)
                order_spinbox.setMaximum(20)
                order_spinbox.valueChanged.connect(
                    lambda val, r=row, bc=barcode: self._update_order(r, bc, val)
                )
                self.shortcuts_table.setCellWidget(row, 2, order_spinbox)

                # Sil butonu
                del_btn = QPushButton("🗑")
                del_btn.setMaximumWidth(40)
                del_btn.clicked.connect(lambda _, bc=barcode: self._remove_shortcut(bc))
                self.shortcuts_table.setCellWidget(row, 3, del_btn)

        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", f"Kısayollar yüklenemedi: {str(e)}")
            logger.error(f"Error loading shortcuts: {e}")

    def _add_shortcut(self):
        """Kısayol ekle."""
        barcode = self.barcode_input.text().strip()
        self.barcode_input.clear()

        if not barcode:
            QMessageBox.warning(self, "Hata", "Lütfen barkod girin!")
            return

        try:
            # Ürün varmı kontrol et
            product = self.db["products"].find_one({"barcode": barcode})
            if not product:
                QMessageBox.warning(self, "Hata", f"Barkod '{barcode}' bulunamadı!")
                return

            # Zaten var mı kontrol et
            dealer = self.db["dealers"].find_one({"code": self.dealer_code})
            shortcuts = dealer.get("shortcut_products", []) if dealer else []

            if any(s.get("barcode") == barcode for s in shortcuts):
                QMessageBox.warning(self, "Hata", "Bu ürün zaten kısayolda!")
                return

            # Ekle
            new_order = len(shortcuts) + 1
            shortcuts.append({"barcode": barcode, "order": new_order})

            self.db.dealers.update_one(
                {"code": self.dealer_code},
                {"$set": {"shortcut_products": shortcuts}}
            )

            self._load_shortcuts()
            QMessageBox.information(self, "Başarılı", f"'{product['name']}' kısayollara eklendi!")

        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", f"Ekleme başarısız: {str(e)}")
            logger.error(f"Error adding shortcut: {e}")

    def _remove_shortcut(self, barcode: str):
        """Kısayol kaldır."""
        try:
            dealer = self.db.dealers.find_one({"code": self.dealer_code})
            shortcuts = dealer.get("shortcut_products", []) if dealer else []

            shortcuts = [s for s in shortcuts if s.get("barcode") != barcode]

            self.db.dealers.update_one(
                {"code": self.dealer_code},
                {"$set": {"shortcut_products": shortcuts}}
            )

            self._load_shortcuts()
            QMessageBox.information(self, "Başarılı", "Kısayol kaldırıldı!")

        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", f"Kaldırma başarısız: {str(e)}")
            logger.error(f"Error removing shortcut: {e}")

    def _update_order(self, row: int, barcode: str, new_order: int):
        """Sırayı güncelle."""
        try:
            dealer = self.db.dealers.find_one({"code": self.dealer_code})
            shortcuts = dealer.get("shortcut_products", []) if dealer else []

            for s in shortcuts:
                if s.get("barcode") == barcode:
                    s["order"] = new_order
                    break

            self.db.dealers.update_one(
                {"code": self.dealer_code},
                {"$set": {"shortcut_products": shortcuts}}
            )

        except PyMongoError as e:
            logger.error(f"Error updating order: {e}")
