"""Genel bakış sayfası — istatistik kartları ve son satışlar."""
from PyQt5.QtWidgets import (
    QGridLayout, QHeaderView, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)


def stat_card(title: str, value: str = "—") -> QWidget:
    card = QWidget(objectName="card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 16, 20, 16)
    title_label = QLabel(title, objectName="cardTitle")
    value_label = QLabel(value, objectName="cardValue")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    card.value_label = value_label
    return card


class DashboardPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        title = QLabel("Genel Bakış", objectName="title")
        layout.addWidget(title)

        cards = QGridLayout()
        cards.setSpacing(16)
        self.card_products = stat_card("TOPLAM ÜRÜN")
        self.card_dealers = stat_card("KAYITLI BAYİ")
        self.card_sales = stat_card("BUGÜNKÜ SATIŞ")
        self.card_revenue = stat_card("BUGÜNKÜ CİRO")
        for i, card in enumerate(
            [self.card_products, self.card_dealers,
             self.card_sales, self.card_revenue]
        ):
            cards.addWidget(card, 0, i)
        layout.addLayout(cards)

        subtitle = QLabel("Son Satışlar", objectName="subtitle")
        layout.addWidget(subtitle)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Tarih", "Bayi", "Ödeme", "Tutar"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

    def refresh(self):
        summary = self.db.daily_summary()
        self.card_products.value_label.setText(str(summary["product_count"]))
        self.card_dealers.value_label.setText(str(summary["dealer_count"]))
        self.card_sales.value_label.setText(str(summary["today_sale_count"]))
        self.card_revenue.value_label.setText(
            f"{summary['today_revenue']:.2f} ₺")

        sales = self.db.get_sales()[:20]
        self.table.setRowCount(len(sales))
        for row, sale in enumerate(sales):
            date = sale.get("date")
            self.table.setItem(row, 0, QTableWidgetItem(
                date.strftime("%d.%m.%Y %H:%M") if date else "—"))
            self.table.setItem(row, 1, QTableWidgetItem(
                sale.get("dealer_code", "—")))
            self.table.setItem(row, 2, QTableWidgetItem(
                sale.get("payment_type", "—")))
            self.table.setItem(row, 3, QTableWidgetItem(
                f"{sale.get('total', 0):.2f} ₺"))
