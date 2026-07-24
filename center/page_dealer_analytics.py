"""Bayı ciro analiz sayfası — tüm bayıların günlük/haftalık/aylık cirosunu görüntüle."""
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis
from PyQt5.QtGui import QColor

from common import style


class DealerAnalyticsPage(QWidget):
    """Merkez: tüm bayıların ciro analitikleri."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("Bayı Ciro Analizi", objectName="title")
        layout.addWidget(title)

        # Bayı seçimi
        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Bayı:"))
        self.dealer_combo = QComboBox()
        self.dealer_combo.addItem("Tüm Bayılar", "")
        for dealer in self.db.get_dealers():
            self.dealer_combo.addItem(
                f"{dealer['code']} — {dealer.get('name', '')}",
                dealer["code"])
        self.dealer_combo.currentIndexChanged.connect(self._refresh_data)
        selector_row.addWidget(self.dealer_combo)

        selector_row.addWidget(QLabel("Dönem:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("Son 30 Gün", "daily")
        self.period_combo.addItem("Son 13 Hafta", "weekly")
        self.period_combo.addItem("Son 12 Ay", "monthly")
        self.period_combo.currentIndexChanged.connect(self._refresh_data)
        selector_row.addWidget(self.period_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        # Grafik
        self.chart = QChart()
        self.chart.setTitle("Ciro Grafiği")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view, 2)

        # Tablo
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Dönem", "Satış Sayısı", "Toplam Ciro"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self._refresh_data()

    def _refresh_data(self):
        """Seçilen dönem ve bayıya göre verileri güncelle."""
        period = self.period_combo.currentData()
        dealer_code = self.dealer_combo.currentData() or ""

        if period == "daily":
            self._show_daily_revenue(dealer_code)
        elif period == "weekly":
            self._show_weekly_revenue(dealer_code)
        elif period == "monthly":
            self._show_monthly_revenue(dealer_code)

    def _get_dealer_name(self, code: str) -> str:
        """Bayı kodundan adını al."""
        for dealer in self.db.get_dealers():
            if dealer["code"] == code:
                return dealer.get("name", code)
        return code

    def _show_daily_revenue(self, dealer_code: str):
        """Son 30 günün günlük cirosunu göster."""
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=30)).replace(hour=0, minute=0, second=0)

        sales = self.db.get_sales(start_date, end_date, dealer_code)

        # Gün bazlı gruplama (dealer_code ise, tüm bayı satışları bir grafik)
        if dealer_code:
            daily_data = {}
            for sale in sales:
                date_key = sale.get("date").strftime("%d.%m")
                daily_data[date_key] = daily_data.get(date_key, 0) + sale.get("total", 0)
            
            dates = []
            for i in range(30, -1, -1):
                d = (datetime.now() - timedelta(days=i)).strftime("%d.%m")
                dates.append(d)
            
            self._plot_chart(dates, [daily_data.get(d, 0) for d in dates], "Günlük Ciro")
            self._populate_table(dates, daily_data)
        else:
            # Tüm bayılar için bar chart (her bayı ayrı set)
            dealer_daily = {}
            for sale in sales:
                dc = sale.get("dealer_code", "Bilinmiyor")
                date_key = sale.get("date").strftime("%d.%m")
                key = f"{dc}|{date_key}"
                dealer_daily[key] = dealer_daily.get(key, 0) + sale.get("total", 0)
            
            dates = []
            for i in range(30, -1, -1):
                d = (datetime.now() - timedelta(days=i)).strftime("%d.%m")
                dates.append(d)
            
            # Her bayı için ayrı bar set
            dealers = self.db.get_dealers()
            series = QBarSeries()
            colors = [style.palette()["accent"], style.palette()["secondary"],
                     style.palette()["green"], style.palette()["yellow"]]
            
            for idx, dealer in enumerate(dealers[:4]):
                dc = dealer["code"]
                bar_set = QBarSet(dc)
                bar_set.setColor(QColor(colors[idx % len(colors)]))
                
                for d in dates:
                    key = f"{dc}|{d}"
                    bar_set.append(dealer_daily.get(key, 0))
                
                series.append(bar_set)
            
            self.chart.removeAllSeries()
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
            self.chart.addSeries(series)
            
            axis_x = QBarCategoryAxis()
            axis_x.append(dates)
            axis_x.setLabelsAngle(-45)
            self.chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            
            axis_y = self.chart.axisY()
            if not axis_y:
                from PyQt5.QtChart import QValueAxis
                axis_y = QValueAxis()
                self.chart.addAxis(axis_y, Qt.AlignLeft)
                series.attachAxis(axis_y)
            
            self.chart.setTitle("Tüm Bayıların Son 30 Günlük Günlük Cirosı")
            
            self.table.setRowCount(0)

    def _show_weekly_revenue(self, dealer_code: str):
        """Son 13 haftanın haftalık cirosunu göster."""
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=91)).replace(hour=0, minute=0, second=0)

        sales = self.db.get_sales(start_date, end_date, dealer_code)

        weekly_data = {}
        for sale in sales:
            date = sale.get("date")
            week_num = date.strftime("Hafta %W")
            weekly_data[week_num] = weekly_data.get(week_num, 0) + sale.get("total", 0)

        weeks = []
        for i in range(12, -1, -1):
            d = datetime.now() - timedelta(weeks=i)
            week_num = d.strftime("Hafta %W")
            weeks.append(week_num)

        self._plot_chart(weeks, [weekly_data.get(w, 0) for w in weeks], "Haftalık Ciro")
        self._populate_table(weeks, weekly_data)

    def _show_monthly_revenue(self, dealer_code: str):
        """Son 12 ayın aylık cirosunu göster."""
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=365)).replace(hour=0, minute=0, second=0)

        sales = self.db.get_sales(start_date, end_date, dealer_code)

        monthly_data = {}
        for sale in sales:
            date = sale.get("date")
            month_key = date.strftime("%m/%Y")
            monthly_data[month_key] = monthly_data.get(month_key, 0) + sale.get("total", 0)

        months = []
        for i in range(11, -1, -1):
            d = datetime.now() - timedelta(days=30*i)
            month_key = d.strftime("%m/%Y")
            months.append(month_key)

        self._plot_chart(months, [monthly_data.get(m, 0) for m in months], "Aylık Ciro")
        self._populate_table(months, monthly_data)

    def _plot_chart(self, labels: list, values: list, title: str):
        """Grafik çiz."""
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        bar_set = QBarSet("Ciro")
        bar_set.setColor(QColor(style.palette()["accent"]))
        
        for v in values:
            bar_set.append(v)

        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsAngle(-45)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = self.chart.axisY()
        if not axis_y:
            from PyQt5.QtChart import QValueAxis
            axis_y = QValueAxis()
            self.chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

        self.chart.setTitle(title)

    def _populate_table(self, labels: list, data: dict):
        """Tablo doldur."""
        self.table.setRowCount(len(labels))
        
        total_sales = 0
        total_amount = sum(data.values())
        
        for row, label in enumerate(labels):
            value = data.get(label, 0)
            cells = [label, "—", f"{value:,.2f} ₺".replace(",", ".").replace(".", ",")]
            for col, text in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(text))
