"""Satış raporları sayfası — tarih/bayi filtresi ve satış detayı."""
from datetime import datetime, timedelta

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class SaleDetailDialog(QDialog):
    """Bir satışın kalemlerini gösteren diyalog."""

    def __init__(self, parent, sale: dict):
        super().__init__(parent)
        date = sale.get("date")
        self.setWindowTitle("Satış Detayı")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        customer_name = sale.get("customer_name", "İsimsiz")
        customer_surname = sale.get("customer_surname", "İsimsiz")
        header = QLabel(
            f"{sale.get('dealer_code', '—')} — "
            f"{customer_name} {customer_surname} — "
            f"{date.strftime('%d.%m.%Y %H:%M') if date else '—'} — "
            f"{sale.get('payment_type', '—')}", objectName="title")
        layout.addWidget(header)

        # Müşteri bilgileri
        info_layout = QHBoxLayout()
        info_fields = [
            ("Tel:", sale.get("customer_phone", "—")),
            ("Doğum:", sale.get("customer_birthdate", "—")),
            ("Yıl Dönümü:", sale.get("customer_anniversary", "—")),
        ]
        for label_text, value in info_fields:
            info_layout.addWidget(QLabel(label_text, objectName="subtitle"))
            info_layout.addWidget(QLabel(value))
            info_layout.addSpacing(16)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(
            ["Ürün", "Adet", "Birim Fiyat", "Tutar"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        items = sale.get("items", [])
        table.setRowCount(len(items))
        for row, item in enumerate(items):
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            cells = [
                item.get("name", item.get("barcode", "?")),
                str(quantity),
                f"{unit_price:.2f} ₺",
                f"{quantity * unit_price:.2f} ₺",
            ]
            for column, text in enumerate(cells):
                table.setItem(row, column, QTableWidgetItem(text))
        layout.addWidget(table, 1)

        total = QLabel(f"Genel Toplam: {sale.get('total', 0):.2f} ₺",
                       objectName="title")
        layout.addWidget(total)

        close_button = QPushButton("Kapat", objectName="primary")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


class ReportsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._sales = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Satış Raporları", objectName="title")
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)
        self.start_date = QDateEdit(QDate.currentDate().addDays(-7),
                                    calendarPopup=True)
        self.end_date = QDateEdit(QDate.currentDate(), calendarPopup=True)
        self.dealer_box = QComboBox()
        self.dealer_box.setMinimumWidth(200)
        filter_button = QPushButton("Filtrele", objectName="primary")
        filter_button.clicked.connect(self.refresh)
        filter_row.addWidget(QLabel("Başlangıç:"))
        filter_row.addWidget(self.start_date)
        filter_row.addWidget(QLabel("Bitiş:"))
        filter_row.addWidget(self.end_date)
        filter_row.addWidget(QLabel("Bayi:"))
        filter_row.addWidget(self.dealer_box)
        filter_row.addWidget(filter_button)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["Tarih", "Bayi", "Müşteri Adı", "Telefon", "Doğum Tarihi", "Yıl Dönümü", "Kalem", "Ödeme", "Tutar"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._show_detail)
        self.table.selectionModel().selectionChanged.connect(self._on_selection)
        layout.addWidget(self.table, 1)

        bottom_row = QHBoxLayout()
        hint = QLabel("Kalem detayı için satıra çift tıklayın ya da seçip butona basın.",
                      objectName="subtitle")
        bottom_row.addWidget(hint, 1)
        self.detail_button = QPushButton("👁  Satış Detayı", objectName="primary")
        self.detail_button.setEnabled(False)
        self.detail_button.clicked.connect(self._show_detail)
        bottom_row.addWidget(self.detail_button)
        layout.addLayout(bottom_row)

        self.summary = QLabel("", objectName="title")
        layout.addWidget(self.summary)

    def _on_selection(self):
        row = self.table.currentRow()
        self.detail_button.setEnabled(0 <= row < len(self._sales))

    def _show_detail(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._sales):
            SaleDetailDialog(self, self._sales[row]).exec_()

    def refresh(self):
        selected_dealer = (self.dealer_box.currentData()
                           if self.dealer_box.count() else "")
        self.dealer_box.blockSignals(True)
        self.dealer_box.clear()
        self.dealer_box.addItem("Tüm Bayiler", "")
        for dealer in self.db.get_dealers():
            self.dealer_box.addItem(
                f"{dealer['code']} — {dealer.get('name', '')}", dealer["code"])
        index = self.dealer_box.findData(selected_dealer)
        if index >= 0:
            self.dealer_box.setCurrentIndex(index)
        self.dealer_box.blockSignals(False)

        start = datetime.combine(self.start_date.date().toPyDate(),
                                 datetime.min.time())
        end = datetime.combine(self.end_date.date().toPyDate(),
                               datetime.min.time()) + timedelta(days=1)
        sales = self.db.get_sales(start, end,
                                  self.dealer_box.currentData() or "")
        self._sales = sales

        self.table.setRowCount(len(sales))
        total = 0.0
        for row, sale in enumerate(sales):
            date = sale.get("date")
            total += sale.get("total", 0)
            customer_name = sale.get("customer_name", "İsimsiz")
            customer_surname = sale.get("customer_surname", "İsimsiz")
            customer_phone = sale.get("customer_phone", "—")
            customer_birthdate = sale.get("customer_birthdate", "—")
            customer_anniversary = sale.get("customer_anniversary", "—")
            cells = [
                date.strftime("%d.%m.%Y %H:%M") if date else "—",
                sale.get("dealer_code", "—"),
                f"{customer_name} {customer_surname}",
                customer_phone,
                customer_birthdate,
                customer_anniversary,
                str(sum(i.get("quantity", 0) for i in sale.get("items", []))),
                sale.get("payment_type", "—"),
                f"{sale.get('total', 0):.2f} ₺",
            ]
            for column, text in enumerate(cells):
                self.table.setItem(row, column, QTableWidgetItem(text))

        self.summary.setText(f"Toplam: {len(sales)} satış — {total:.2f} ₺")
