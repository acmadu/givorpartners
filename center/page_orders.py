"""Merkezde gelen siparişleri ve iade taleplerini yönetme sayfası."""
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)
from bson import ObjectId
from pymongo.errors import PyMongoError


class OrderDialog(QDialog):
    """Sipariş detaylarını gösterme ve durum değiştirme."""

    def __init__(self, parent, db, order: dict):
        super().__init__(parent)
        self.db = db
        self.order = order
        self.setWindowTitle("Sipariş Detayları")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Bilgiler
        form = QFormLayout()
        form.addRow("Sipariş ID:", QLabel(str(order["_id"])))
        form.addRow("Bayi:", QLabel(order.get("dealer_name", "?")))
        form.addRow("Tarih:", QLabel(
            order.get("created_at").strftime("%d.%m.%Y %H:%M")
            if order.get("created_at") else "?"))
        form.addRow("Tutar:", QLabel(f"{order.get('total', 0):.2f} ₺"))

        # Ürünler
        form.addRow("Ürünler:", QLabel(""))
        items_text = "\n".join([
            f"• {item['name']}: {item['quantity_boxes']} koli × {item['unit_price']:.2f} ₺"
            for item in order.get("items", [])
        ])
        items_label = QLabel(items_text)
        form.addRow("", items_label)

        # Durum
        form.addRow("Notlar:", QLabel(order.get("notes", "—")))

        layout.addLayout(form)
        layout.addStretch()

        # Durum değiştirme
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            ("Beklemede", "pending"),
            ("Onaylandı", "confirmed"),
            ("Gönderildi", "shipped"),
            ("Teslim Edildi", "delivered"),
            ("İptal Edildi", "cancelled"),
        ])
        current_status = order.get("status", "pending")
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == current_status:
                self.status_combo.setCurrentIndex(i)
                break
        status_row.addWidget(self.status_combo)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Güncelle")
        buttons.button(QDialogButtonBox.Cancel).setText("Kapat")
        buttons.accepted.connect(self._update_status)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_status(self):
        """Siparişin durumunu güncelle."""
        try:
            new_status = self.status_combo.currentData()
            self.db.update_order_status(ObjectId(str(self.order["_id"])), new_status)
            
            # Delivered durumuna geçerken, stok otomatik olarak bayiye eklenir
            if new_status == "delivered":
                dealer_code = self.order.get("dealer_code")
                for item in self.order.get("items", []):
                    barcode = item['barcode']
                    qty = item['quantity_boxes'] * item.get('unit_quantity', 1)
                    # Bayi stoğuna ürün ekle
                    self.db.dealer_stocks.update_one(
                        {"dealer_code": dealer_code, "barcode": barcode},
                        {"$inc": {"stock": qty}},
                        upsert=True)
                QMessageBox.information(
                    self, "✓ Teslim Edildi",
                    "Sipariş teslim edildi.\nÜrünler bayi stoğuna eklendi.")
            else:
                QMessageBox.information(self, "Başarılı", "Sipariş durumu güncellendi.")
            self.accept()
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Güncellenemedi:\n{error}")


class ReturnDialog(QDialog):
    """İade talebini gösterme, onaylama/reddetme."""

    def __init__(self, parent, db, return_obj: dict):
        super().__init__(parent)
        self.db = db
        self.return_obj = return_obj
        return_type = return_obj.get("type", "customer_return")
        title = "Sipariş İadesi" if return_type == "order_return" else "Müşteri İadesi"
        self.setWindowTitle(title)
        self.setMinimumSize(550, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Bilgiler
        form = QFormLayout()
        form.addRow("İade ID:", QLabel(str(return_obj["_id"])))
        form.addRow("Bayi:", QLabel(return_obj.get("dealer_name", "?")))
        form.addRow("Tarih:", QLabel(
            return_obj.get("created_at").strftime("%d.%m.%Y %H:%M")
            if return_obj.get("created_at") else "?"))

        if return_type == "order_return" and return_obj.get("order_id"):
            form.addRow("Sipariş ID:", QLabel(str(return_obj.get("order_id"))[:8]))

        # İade ürünleri
        form.addRow("İade Edilen Ürünler:", QLabel(""))
        items_text = "\n".join([
            f"• {item['name']} ({item['barcode']}): {item['quantity']} adet\n"
            f"  Neden: {item.get('reason', '—')}"
            for item in return_obj.get("items", [])
        ])
        items_label = QLabel(items_text)
        form.addRow("", items_label)

        if return_obj.get("notes"):
            form.addRow("Not:", QLabel(return_obj.get("notes")))

        layout.addLayout(form)
        layout.addStretch()

        # Durum değiştirme
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Karar:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            ("Beklemede", "pending"),
            ("Onaylandı", "approved"),
            ("Reddedildi", "rejected"),
        ])
        current_status = return_obj.get("status", "pending")
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == current_status:
                self.status_combo.setCurrentIndex(i)
                break
        status_row.addWidget(self.status_combo)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Güncelle")
        buttons.button(QDialogButtonBox.Cancel).setText("Kapat")
        buttons.accepted.connect(self._update_status)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_status(self):
        """İade talebini güncelle ve onaylandıysa ürünleri stoka ekle."""
        try:
            new_status = self.status_combo.currentData()
            self.db.update_return_status(
                ObjectId(str(self.return_obj["_id"])), new_status)

            # Onaylandıysa ürünleri stoka geri ekle
            if new_status == "approved":
                for item in self.return_obj.get("items", []):
                    barcode = item.get("barcode", "")
                    qty = item.get("quantity", 0)
                    if barcode and qty > 0:
                        self.db.products.update_one(
                            {"barcode": barcode},
                            {"$inc": {"stock": qty}})

            QMessageBox.information(self, "Başarılı", "İade talebı güncellendi.")
            self.accept()
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Güncellenemedi:\n{error}")


class OrdersPage(QWidget):
    """Gelen siparişleri ve iade taleplerini yönetme."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Başlık
        top = QHBoxLayout()
        title = QLabel("📋 Siparişler ve İadeler", objectName="title")
        refresh = QPushButton("🔄 Yenile")
        refresh.clicked.connect(self.refresh)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(refresh)
        layout.addLayout(top)

        # Sekmeler
        tabs = QHBoxLayout()
        self.orders_btn = QPushButton("📦 Siparişler", checkable=True)
        self.orders_btn.setChecked(True)
        self.returns_btn = QPushButton("🔄 İade Talepleri", checkable=True)
        self.orders_btn.clicked.connect(self._show_orders)
        self.returns_btn.clicked.connect(self._show_returns)
        tabs.addWidget(self.orders_btn)
        tabs.addWidget(self.returns_btn)
        tabs.addStretch()
        layout.addLayout(tabs)

        # Tablo
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Bayi", "Tarih", "Tutar", "Ürün", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._open_item)
        layout.addWidget(self.table, 1)

        # Butonlar
        bottom = QHBoxLayout()
        self.approve_btn = QPushButton("✔ Onayla")
        self.approve_btn.clicked.connect(self._approve_item)
        self.cancel_btn = QPushButton("✖ İptal Et", objectName="danger")
        self.cancel_btn.clicked.connect(self._cancel_item)
        bottom.addStretch()
        bottom.addWidget(self.approve_btn)
        bottom.addWidget(self.cancel_btn)
        layout.addLayout(bottom)

        self._current_mode = "orders"
        self.refresh()

    def _show_orders(self):
        """Siparişler modunu göster."""
        self.orders_btn.setChecked(True)
        self.returns_btn.setChecked(False)
        self._current_mode = "orders"
        self.refresh()

    def _show_returns(self):
        """İade talepleri modunu göster."""
        self.orders_btn.setChecked(False)
        self.returns_btn.setChecked(True)
        self._current_mode = "returns"
        self.refresh()

    def refresh(self):
        """Tabloyu yenile."""
        self.table.setRowCount(0)
        try:
            if self._current_mode == "orders":
                items = self.db.get_orders()
                for row, order in enumerate(items):
                    self.table.insertRow(row)
                    order_id = str(order["_id"])[:8]
                    dealer = order.get("dealer_name", "?")
                    date_str = order.get("created_at").strftime("%d.%m.%Y %H:%M") if order.get("created_at") else "?"
                    total = f"{order.get('total', 0):.2f} ₺"
                    items_count = str(len(order.get("items", [])))
                    status = order.get("status", "?")
                    cells = [order_id, dealer, date_str, total, items_count, status]
                    for col, text in enumerate(cells):
                        item = QTableWidgetItem(text)
                        if status == "pending":
                            item.setForeground(QColor("#ffc107"))  # Sarı
                        elif status in ("confirmed", "shipped"):
                            item.setForeground(QColor("#17a2b8"))  # Turkuaz
                        self.table.setItem(row, col, item)
            else:  # returns
                items = self.db.get_returns()
                for row, ret in enumerate(items):
                    self.table.insertRow(row)
                    return_id = str(ret["_id"])[:8]
                    dealer = ret.get("dealer_name", "?")
                    date_str = ret.get("created_at").strftime("%d.%m.%Y %H:%M") if ret.get("created_at") else "?"
                    total = f"{len(ret.get('items', []))} ürün"
                    return_type = ret.get("type", "customer_return")
                    type_label = "Sipariş" if return_type == "order_return" else "Müşteri"
                    status = ret.get("status", "?")
                    cells = [return_id, dealer, date_str, total, type_label, status]
                    for col, text in enumerate(cells):
                        item = QTableWidgetItem(text)
                        if status == "pending":
                            item.setForeground(QColor("#ffc107"))  # Sarı
                        elif status == "approved":
                            item.setForeground(QColor("#28a745"))  # Yeşil
                        self.table.setItem(row, col, item)
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Yüklenemedi:\n{error}")

    def _open_item(self):
        """Seçili öğeyi aç."""
        row = self.table.currentRow()
        if row < 0:
            return
        try:
            if self._current_mode == "orders":
                orders = self.db.get_orders()
                if row < len(orders):
                    dialog = OrderDialog(self, self.db, orders[row])
                    if dialog.exec_() == QDialog.Accepted:
                        self.refresh()
            else:  # returns
                returns = self.db.get_returns()
                if row < len(returns):
                    dialog = ReturnDialog(self, self.db, returns[row])
                    if dialog.exec_() == QDialog.Accepted:
                        self.refresh()
        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Açılamadı:\n{error}")

    def _approve_item(self):
        """Seçili öğeyi onayla."""
        row = self.table.currentRow()
        if row < 0:
            return
        try:
            if self._current_mode == "orders":
                orders = self.db.get_orders(status="pending")
                if row < len(orders):
                    self.db.update_order_status(
                        ObjectId(str(orders[row]["_id"])), "confirmed")
            else:
                returns = self.db.get_returns(status="pending")
                if row < len(returns):
                    ret = returns[row]
                    # İade onaylandı, ürünleri stoka ekle
                    for item in ret.get("items", []):
                        barcode = item.get("barcode", "")
                        qty = item.get("quantity", 0)
                        if barcode and qty > 0:
                            self.db.products.update_one(
                                {"barcode": barcode},
                                {"$inc": {"stock": qty}})
                    self.db.update_return_status(
                        ObjectId(str(ret["_id"])), "approved")
            self.refresh()
        except Exception as error:
            QMessageBox.critical(self, "Hata", str(error))

    def _cancel_item(self):
        """Seçili öğeyi iptal et."""
        row = self.table.currentRow()
        if row < 0:
            return
        answer = QMessageBox.question(
            self, "İptal", "Emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            try:
                if self._current_mode == "orders":
                    orders = self.db.get_orders()
                    if row < len(orders):
                        self.db.update_order_status(
                            ObjectId(str(orders[row]["_id"])), "cancelled")
                else:
                    returns = self.db.get_returns()
                    if row < len(returns):
                        self.db.update_return_status(
                            ObjectId(str(returns[row]["_id"])), "rejected")
                self.refresh()
            except Exception as error:
                QMessageBox.critical(self, "Hata", str(error))
