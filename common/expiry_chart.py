"""Son Kullanım Tarihi uyarı grafiği — Merkez ve Bayi için kullanılır."""
from datetime import date, datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QWidget,
)
from PyQt5.QtChart import (
    QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis,
)
from pymongo.errors import PyMongoError


class ExpiryChartWidget(QWidget):
    """SKT uyarı grafiği widget — her iki tarafta da kullanılır."""

    WARNING_DAYS = 90  # 90 gün içinde sona erenler uyarı gösterir

    def __init__(self, db, dealer_code: str = "", parent=None):
        """
        dealer_code: boş string → merkez (tüm ürünler)
                     dolu       → bayi (bayi stoğundaki ürünler)
        """
        super().__init__(parent)
        self.db = db
        self.dealer_code = dealer_code

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top = QHBoxLayout()
        if dealer_code:
            title = QLabel("Son Kullanım Tarihi Uyarıları — Depom", objectName="title")
        else:
            title = QLabel("Son Kullanım Tarihi Uyarıları — Tüm Ürünler", objectName="title")
        top.addWidget(title)
        top.addStretch()
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        # Grafik
        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(280)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view, 1)

        # Tablo
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Ürün Adı", "Barkod", "SKT", "Kalan Gün", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        today = date.today()

        try:
            if self.dealer_code:
                # Bayide: dealer_stocks + ürün bilgileri
                stock_docs = list(self.db.dealer_stocks.find(
                    {"dealer_code": self.dealer_code, "stock": {"$gt": 0}}))
                barcodes = [d['barcode'] for d in stock_docs]
                products = list(self.db.products.find(
                    {"barcode": {"$in": barcodes}, "expiry_date": {"$exists": True}}))
            else:
                # Merkez: tüm ürünler
                products = list(self.db.products.find(
                    {"expiry_date": {"$exists": True}}))

            # SKT olan ürünleri filtrele ve sırala
            expiry_products = []
            for p in products:
                expiry = p.get('expiry_date')
                if not expiry:
                    continue
                if isinstance(expiry, datetime):
                    expiry = expiry.date()
                days_left = (expiry - today).days
                if days_left <= self.WARNING_DAYS:
                    expiry_products.append((p, expiry, days_left))

            expiry_products.sort(key=lambda x: x[2])

            # Grafik: Her ürün için kalan gün bar grafiği
            chart = QChart()
            chart.setTitle(f"SKT Yaklaşan Ürünler (son {self.WARNING_DAYS} gün)")
            chart.setAnimationOptions(QChart.SeriesAnimations)

            if expiry_products:
                expired_set = QBarSet("Süresi Dolmuş")
                expired_set.setColor(QColor("#dc2626"))
                warning_set = QBarSet("30 Günden Az")
                warning_set.setColor(QColor("#f59e0b"))
                safe_set = QBarSet("Güvende")
                safe_set.setColor(QColor("#10b981"))

                categories = []
                for p, expiry, days_left in expiry_products[:12]:  # max 12 ürün
                    name = p['name'][:12]
                    categories.append(name)
                    if days_left < 0:
                        expired_set.append(max(0, -days_left))
                        warning_set.append(0)
                        safe_set.append(0)
                    elif days_left <= 30:
                        expired_set.append(0)
                        warning_set.append(days_left)
                        safe_set.append(0)
                    else:
                        expired_set.append(0)
                        warning_set.append(0)
                        safe_set.append(days_left)

                series = QBarSeries()
                series.append(expired_set)
                series.append(warning_set)
                series.append(safe_set)
                chart.addSeries(series)

                axis_x = QBarCategoryAxis()
                axis_x.append(categories)
                chart.addAxis(axis_x, Qt.AlignBottom)
                series.attachAxis(axis_x)

                axis_y = QValueAxis()
                axis_y.setTitleText("Kalan Gün")
                chart.addAxis(axis_y, Qt.AlignLeft)
                series.attachAxis(axis_y)

                chart.legend().setVisible(True)
            else:
                chart.setTitle("Uyarı gerektiren ürün yok ✓")

            self.chart_view.setChart(chart)

            # Tablo
            for p, expiry, days_left in expiry_products:
                row = self.table.rowCount()
                self.table.insertRow(row)
                if days_left < 0:
                    durum = "⛔ SÜRESI DOLDU"
                    color = "#dc2626"
                elif days_left <= 30:
                    durum = "⚠ Çok Yakın"
                    color = "#f59e0b"
                else:
                    durum = "⚠ Yaklaşıyor"
                    color = "#f59e0b"

                cells = [
                    p['name'],
                    p['barcode'],
                    expiry.strftime("%m/%Y"),
                    str(days_left),
                    durum,
                ]
                for col, text in enumerate(cells):
                    item = QTableWidgetItem(text)
                    item.setForeground(QColor(color))
                    self.table.setItem(row, col, item)

        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", f"Yüklenemedi:\n{e}")
