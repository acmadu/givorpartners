"""Merkez: Her bayinin stoğunu grafik ile görüntüleme."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QHeaderView, QPushButton,
)
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from pymongo.errors import PyMongoError


class DealerStockChartPage(QWidget):
    """Merkez'de her bayinin stok durumunu grafik olarak göster."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top = QHBoxLayout()
        title = QLabel("Bayi Stok Grafikleri", objectName="title")
        top.addWidget(title)
        top.addStretch()

        # Bayi seçimi
        top.addWidget(QLabel("Bayi:"))
        self.dealer_combo = QComboBox()
        self.dealer_combo.setMinimumWidth(200)
        self.dealer_combo.addItem("Tüm Bayiler", "")
        self.dealer_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.dealer_combo)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._reload_dealers)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        # Grafik alanı
        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(350)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view, 2)

        # Tablo
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Bayi", "Ürün Adı", "Stok", "Birim"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self._reload_dealers()

    def _reload_dealers(self):
        """Bayi listesini güncelle."""
        self.dealer_combo.blockSignals(True)
        prev = self.dealer_combo.currentData()
        self.dealer_combo.clear()
        self.dealer_combo.addItem("Tüm Bayiler", "")
        try:
            for d in self.db.dealers.find({}):
                self.dealer_combo.addItem(d['name'], d['code'])
        except PyMongoError:
            pass
        idx = self.dealer_combo.findData(prev)
        if idx >= 0:
            self.dealer_combo.setCurrentIndex(idx)
        self.dealer_combo.blockSignals(False)
        self.refresh()

    def refresh(self):
        """Seçili bayinin stok grafiğini çiz."""
        self.table.setRowCount(0)
        dealer_code = self.dealer_combo.currentData()

        try:
            query = {"dealer_code": dealer_code} if dealer_code else {}
            docs = list(self.db.dealer_stocks.find(query))

            if not docs:
                self.chart_view.setChart(QChart())
                return

            # Ürün adları ve stok miktarları
            categories = []
            values = {}  # dealer_code → {barcode: stock}

            for doc in docs:
                product = self.db.products.find_one({"barcode": doc['barcode']})
                name = product['name'][:15] if product else doc['barcode']
                stock = doc.get('stock', 0)
                dcode = doc['dealer_code']

                if dcode not in values:
                    values[dcode] = {}
                values[dcode][name] = stock
                if name not in categories:
                    categories.append(name)

            # Bar chart oluştur
            chart = QChart()
            chart.setTitle(f"Stok — {self.dealer_combo.currentText()}")
            chart.setAnimationOptions(QChart.SeriesAnimations)

            series = QBarSeries()
            colors = [
                QColor("#3b82f6"), QColor("#10b981"), QColor("#f59e0b"),
                QColor("#ec4899"), QColor("#8b5cf6"), QColor("#06b6d4"),
            ]

            for i, (dcode, stock_map) in enumerate(values.items()):
                dealer_doc = self.db.dealers.find_one({"code": dcode})
                bar_label = dealer_doc['name'] if dealer_doc else dcode
                bar_set = QBarSet(bar_label)
                bar_set.setColor(colors[i % len(colors)])
                for cat in categories:
                    bar_set.append(stock_map.get(cat, 0))
                series.append(bar_set)

            chart.addSeries(series)

            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setTitleText("Adet")
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

            chart.legend().setVisible(len(values) > 1)
            self.chart_view.setChart(chart)

            # Tabloyu doldur
            row = 0
            for doc in docs:
                product = self.db.products.find_one({"barcode": doc['barcode']})
                dealer_doc = self.db.dealers.find_one({"code": doc['dealer_code']})
                dealer_name = dealer_doc['name'] if dealer_doc else doc['dealer_code']
                name = product['name'] if product else doc['barcode']
                unit = product.get('unit', 'adet') if product else 'adet'
                stock = doc.get('stock', 0)

                self.table.insertRow(row)
                for col, text in enumerate([dealer_name, name, str(stock), unit]):
                    item = QTableWidgetItem(text)
                    if stock < 20:
                        item.setForeground(QColor("#dc2626"))
                    elif stock < 50:
                        item.setForeground(QColor("#f59e0b"))
                    self.table.setItem(row, col, item)
                row += 1

        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", f"Yüklenemedi:\n{e}")
