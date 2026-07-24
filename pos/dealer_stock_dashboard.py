"""Bayi'nin kendi stok durumunu grafik olarak görmesi."""
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox,
)
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtCore import QPointF
from pymongo.errors import PyMongoError


class DealerStockDashboard(QDialog):
    """Bayi'nin stok durumunu grafik ve tablo ile göster."""

    def __init__(self, parent, db, dealer_code: str, dealer_name: str):
        super().__init__(parent)
        self.db = db
        self.dealer_code = dealer_code
        self.dealer_name = dealer_name
        self.setWindowTitle(f"📦  Depo Durumu — {dealer_name}")
        self.setMinimumSize(1000, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Başlık
        title = QLabel(f"Depo Durumu: {dealer_name}")
        title.setFont(QFont("", 14, QFont.Bold))
        main_layout.addWidget(title)

        # İstatistikler
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("Toplam: — adet")
        self.warning_label = QLabel("Uyarı: — ürün (<50 adet)")
        self.warning_label.setStyleSheet("color: #dc2626;")  # Kırmızı
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.warning_label)
        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        # İçerik: Grafik sol, Tablo sağ
        content = QHBoxLayout()

        # Pasta grafik (stok dağılımı)
        chart_view = self._create_pie_chart()
        content.addWidget(chart_view, 1)

        # Tablo (en düşük stoklar)
        table = self._create_stock_table()
        content.addWidget(table, 1)

        main_layout.addLayout(content, 1)

    def _create_pie_chart(self) -> QChartView:
        """Ürünlerin stok yüzdeleri pasta grafik."""
        chart = QChart()
        chart.setTitle("Ürün Stok Dağılımı")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#ffffff"))
        chart.titleFont().setPointSize(12)

        try:
            docs = list(self.db.dealer_stocks.find({"dealer_code": self.dealer_code}))
            if not docs:
                chart.setTitle("Stok Yok")
                view = QChartView(chart)
                view.setRenderHint(QPainter.Antialiasing)
                return view

            series = QPieSeries()
            colors = [
                QColor("#ec4899"),  # Pink
                QColor("#f59e0b"),  # Amber
                QColor("#10b981"),  # Green
                QColor("#3b82f6"),  # Blue
                QColor("#8b5cf6"),  # Purple
                QColor("#06b6d4"),  # Cyan
            ]

            total = 0
            low_stock_count = 0

            for idx, doc in enumerate(docs):
                barcode = doc['barcode']
                qty = doc.get('stock', 0)
                total += qty

                if qty < 50:
                    low_stock_count += 1

                # Ürün adı bul
                product = self.db.products.find_one({"barcode": barcode})
                name = product['name'] if product else barcode

                slice_ = series.append(name, qty)
                slice_.setColor(colors[idx % len(colors)])
                slice_.setLabel(f"{name}\n({qty})")
                slice_.setLabelVisible(True)

            chart.addSeries(series)
            self.total_label.setText(f"Toplam: {total} adet")
            self.warning_label.setText(f"Uyarı: {low_stock_count} ürün (<50 adet)")

        except PyMongoError as error:
            QMessageBox.critical(None, "Hata", f"Stok alınamadı:\n{error}")

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        return view

    def _create_stock_table(self) -> QTableWidget:
        """En düşük stoklar tablosu."""
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Ürün Adı", "Barkod", "Stok", "Birim"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)

        try:
            # En düşük stoklar (<100) sorgusu
            docs = list(self.db.dealer_stocks.find(
                {"dealer_code": self.dealer_code, "stock": {"$lt": 100}}
            ).sort("stock", 1).limit(10))

            for doc in docs:
                barcode = doc['barcode']
                qty = doc['stock']

                # Ürün detayları
                product = self.db.products.find_one({"barcode": barcode})
                if not product:
                    continue

                row = table.rowCount()
                table.insertRow(row)

                cells = [
                    product['name'],
                    barcode,
                    str(qty),
                    product.get('unit', 'adet'),
                ]

                for col, text in enumerate(cells):
                    item = QTableWidgetItem(text)
                    if qty < 20:
                        item.setForeground(QColor("#dc2626"))  # Kırmızı
                    elif qty < 50:
                        item.setForeground(QColor("#f59e0b"))  # Sarı
                    table.setItem(row, col, item)

        except PyMongoError:
            pass

        return table
