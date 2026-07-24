"""Bayı ciro analizi — günlük, haftalık, aylık grafikleri."""
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox,
)
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis
from PyQt5.QtGui import QColor

from common import style


class DealerAnalyticsDialog(QDialog):
    """Bayı kendi cirosunu günlük/haftalık/aylık görebildiği dialog."""

    def __init__(self, parent, db, dealer_code: str):
        super().__init__(parent)
        self.db = db
        self.dealer_code = dealer_code
        self.setWindowTitle(f"Ciro Analizi — {dealer_code}")
        self.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("Ciro Raporu", objectName="title")
        layout.addWidget(title)

        # Dönem seçimi
        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Dönem:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("Son 30 Gün (Günlük)", "daily")
        self.period_combo.addItem("Son 13 Hafta (Haftalık)", "weekly")
        self.period_combo.addItem("Son 12 Ay (Aylık)", "monthly")
        self.period_combo.currentIndexChanged.connect(self._refresh_chart)
        selector_row.addWidget(self.period_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        # Grafik
        self.chart = QChart()
        self.chart.setTitle("Ciro Grafiği")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(chart_view, 1)

        # Kapatma butonu
        close_btn = QPushButton("Kapat", objectName="primary")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._refresh_chart()

    def _refresh_chart(self):
        """Seçilen döneme göre grafik güncelle."""
        period = self.period_combo.currentData()
        
        if period == "daily":
            self._show_daily_revenue()
        elif period == "weekly":
            self._show_weekly_revenue()
        elif period == "monthly":
            self._show_monthly_revenue()

    def _show_daily_revenue(self):
        """Son 30 günün günlük cirosunu göster."""
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        # 30 gün öncesinden bugüne satışları al
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=30)).replace(
            hour=0, minute=0, second=0)

        sales = self.db.get_sales(start_date, end_date, self.dealer_code)

        # Gün bazlı gruplama
        daily_revenue = {}
        for sale in sales:
            date_key = sale.get("date").strftime("%d.%m")
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + sale.get("total", 0)

        # Son 30 günü oluştur (boş günler de dâhil)
        dates = []
        for i in range(30, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%d.%m")
            dates.append(d)

        # Bar set
        bar_set = QBarSet("Ciro")
        bar_set.setColor(QColor(style.palette()["accent"]))
        
        values = [daily_revenue.get(d, 0) for d in dates]
        for v in values:
            bar_set.append(v)

        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)

        # Eksenler
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

        self.chart.setTitle("Son 30 Günün Günlük Cirosı")

    def _show_weekly_revenue(self):
        """Son 13 haftanın haftalık cirosunu göster."""
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=91)).replace(
            hour=0, minute=0, second=0)

        sales = self.db.get_sales(start_date, end_date, self.dealer_code)

        # Hafta bazlı gruplama
        weekly_revenue = {}
        for sale in sales:
            date = sale.get("date")
            week_num = date.strftime("Hafta %W")
            weekly_revenue[week_num] = weekly_revenue.get(week_num, 0) + sale.get("total", 0)

        # Son 13 haftayı oluştur
        weeks = []
        for i in range(12, -1, -1):
            d = datetime.now() - timedelta(weeks=i)
            week_num = d.strftime("Hafta %W")
            weeks.append(week_num)

        # Bar set
        bar_set = QBarSet("Ciro")
        bar_set.setColor(QColor(style.palette()["secondary"]))
        
        values = [weekly_revenue.get(w, 0) for w in weeks]
        for v in values:
            bar_set.append(v)

        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)

        # Eksenler
        axis_x = QBarCategoryAxis()
        axis_x.append(weeks)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = self.chart.axisY()
        if not axis_y:
            from PyQt5.QtChart import QValueAxis
            axis_y = QValueAxis()
            self.chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

        self.chart.setTitle("Son 13 Haftanın Haftalık Cirosı")

    def _show_monthly_revenue(self):
        """Son 12 ayın aylık cirosunu göster."""
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = (end_date - timedelta(days=365)).replace(
            hour=0, minute=0, second=0)

        sales = self.db.get_sales(start_date, end_date, self.dealer_code)

        # Ay bazlı gruplama
        monthly_revenue = {}
        for sale in sales:
            date = sale.get("date")
            month_key = date.strftime("%m/%Y")
            monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + sale.get("total", 0)

        # Son 12 ayı oluştur
        months = []
        for i in range(11, -1, -1):
            d = datetime.now() - timedelta(days=30*i)
            month_key = d.strftime("%m/%Y")
            months.append(month_key)

        # Bar set
        bar_set = QBarSet("Ciro")
        bar_set.setColor(QColor(style.palette()["green"]))
        
        values = [monthly_revenue.get(m, 0) for m in months]
        for v in values:
            bar_set.append(v)

        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)

        # Eksenler
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = self.chart.axisY()
        if not axis_y:
            from PyQt5.QtChart import QValueAxis
            axis_y = QValueAxis()
            self.chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

        self.chart.setTitle("Son 12 Ayın Aylık Cirosı")
