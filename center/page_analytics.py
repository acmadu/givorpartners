"""Satış analizi sayfası — günlük ciro, cari (bayi) ve ödeme türü grafikleri.

Tüm grafikler QPainter ile çizilir; harici kütüphane gerekmez.
"""
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from common import style


def _money(value: float) -> str:
    return (f"{value:,.2f} ₺".replace(",", "X")
            .replace(".", ",").replace("X", "."))


class DailyRevenueChart(QWidget):
    """Günlük ciroyu dikey çubuklarla çizer."""

    def __init__(self):
        super().__init__()
        self._data = []  # [(etiket, ciro, adet), ...]
        self.setMinimumHeight(240)

    def set_data(self, data: list):
        self._data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pal = style.palette()

        if not self._data or all(t == 0 for _, t, _ in self._data):
            painter.setPen(QColor(pal["muted"]))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "Bu dönemde satış yok.")
            return

        top_pad, bottom_pad, side_pad = 26, 34, 8
        chart_h = self.height() - top_pad - bottom_pad
        highest = max(t for _, t, _ in self._data) or 1
        n = len(self._data)
        slot = (self.width() - side_pad * 2) / n
        bar_w = max(min(slot * 0.66, 46), 3)

        small = QFont(self.font())
        small.setPointSize(8)
        painter.setFont(small)

        # Yatay kılavuz çizgileri
        painter.setPen(QColor(pal["border"]))
        for frac in (0.25, 0.5, 0.75, 1.0):
            y = top_pad + chart_h * (1 - frac)
            painter.drawLine(side_pad, int(y), self.width() - side_pad, int(y))

        label_step = max(1, n // 12)  # etiketler sığsın
        for i, (label, total, _count) in enumerate(self._data):
            x = side_pad + slot * i + (slot - bar_w) / 2
            h = chart_h * (total / highest)
            bar = QRectF(x, top_pad + chart_h - h, bar_w, h)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(pal["accent"]))
            painter.drawRoundedRect(bar, 3, 3)

            painter.setPen(QColor(pal["muted"]))
            if i % label_step == 0:
                painter.drawText(
                    QRectF(side_pad + slot * i, top_pad + chart_h + 4,
                           slot, 22),
                    Qt.AlignCenter, label)
            if total > 0 and slot >= 34:
                painter.setPen(QColor(pal["text"]))
                painter.drawText(
                    QRectF(side_pad + slot * i, bar.top() - 18, slot, 16),
                    Qt.AlignCenter, f"{total:.0f}")


class HBarChart(QWidget):
    """Etiket + yatay çubuk + değer satırlarından oluşan genel grafik."""

    ROW_HEIGHT = 36
    LABEL_WIDTH = 190

    def __init__(self, value_width: int = 240):
        super().__init__()
        self.value_width = value_width
        self._rows = []  # [(etiket, değer, sağ_yazı, renk_anahtarı), ...]

    def set_rows(self, rows: list):
        self._rows = rows
        self.setMinimumHeight(max(len(rows), 1) * self.ROW_HEIGHT + 16)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pal = style.palette()

        if not self._rows:
            painter.setPen(QColor(pal["muted"]))
            painter.drawText(self.rect(), Qt.AlignCenter, "Veri yok.")
            return

        highest = max(max(v for _, v, _, _ in self._rows), 1)
        bar_area = self.width() - self.LABEL_WIDTH - self.value_width - 16

        font = QFont(self.font())
        font.setPointSize(10)
        painter.setFont(font)

        for i, (label, value, right_text, color_key) in enumerate(self._rows):
            y = 8 + i * self.ROW_HEIGHT

            painter.setPen(QColor(pal["text"]))
            painter.drawText(
                QRectF(0, y, self.LABEL_WIDTH - 10, self.ROW_HEIGHT - 10),
                Qt.AlignRight | Qt.AlignVCenter,
                label if len(label) <= 24 else label[:23] + "…")

            track = QRectF(self.LABEL_WIDTH, y + 5, bar_area,
                           self.ROW_HEIGHT - 16)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(pal["card"]))
            painter.drawRoundedRect(track, 6, 6)

            width = bar_area * (max(value, 0) / highest)
            if width > 0:
                bar = QRectF(self.LABEL_WIDTH, y + 5, max(width, 4),
                             self.ROW_HEIGHT - 16)
                painter.setBrush(QColor(pal[color_key]))
                painter.drawRoundedRect(bar, 6, 6)

            painter.setPen(QColor(pal["text"]))
            painter.drawText(
                QRectF(self.LABEL_WIDTH + bar_area + 8, y,
                       self.value_width, self.ROW_HEIGHT - 10),
                Qt.AlignLeft | Qt.AlignVCenter, right_text)


def _section(title: str, widget: QWidget) -> QWidget:
    card = QWidget(objectName="card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.addWidget(QLabel(title, objectName="cardTitle"))
    layout.addWidget(widget)
    return card


class AnalyticsPage(QWidget):
    PERIODS = [("Son 7 gün", 7), ("Son 30 gün", 30), ("Son 90 gün", 90)]

    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top = QHBoxLayout()
        title = QLabel("Satış Analizi", objectName="title")
        self.period_box = QComboBox()
        for label, days in self.PERIODS:
            self.period_box.addItem(label, days)
        self.period_box.setCurrentIndex(1)
        self.period_box.currentIndexChanged.connect(self.refresh)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(QLabel("Dönem:", objectName="subtitle"))
        top.addWidget(self.period_box)
        layout.addLayout(top)

        self.summary_label = QLabel("", objectName="subtitle")
        layout.addWidget(self.summary_label)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        self.daily_chart = DailyRevenueChart()
        self.dealer_chart = HBarChart(value_width=310)
        self.payment_chart = HBarChart(value_width=260)
        content_layout.addWidget(_section("GÜNLÜK CİRO", self.daily_chart))
        content_layout.addWidget(
            _section("CARİ DAĞILIM — BAYİ BAZINDA CİRO", self.dealer_chart))
        content_layout.addWidget(
            _section("ÖDEME TÜRÜ DAĞILIMI", self.payment_chart))
        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

    def refresh(self):
        days = self.period_box.currentData() or 30

        daily = self.db.sales_by_day(days)
        self.daily_chart.set_data(daily)

        dealers = self.db.dealer_account_summary(days)
        self.dealer_chart.set_rows([
            (f"{d['code']} {d['name']}", d["total"],
             f"{_money(d['total'])}  ({d['count']} satış)"
             + (f" — son: {d['last_sale']:%d.%m.%Y}" if d["last_sale"] else ""),
             "accent" if d["total"] > 0 else "border")
            for d in dealers
        ])

        payments = self.db.payment_type_summary(days)
        total_all = sum(t for _, t, _ in payments) or 1
        colors = {"NAKİT": "green", "KART": "secondary"}
        self.payment_chart.set_rows([
            (ptype, total,
             f"{_money(total)}  (%{100 * total / total_all:.0f} — {count} satış)",
             colors.get(ptype, "yellow"))
            for ptype, total, count in payments
        ])

        revenue = sum(t for _, t, _ in daily)
        count = sum(c for _, _, c in daily)
        self.summary_label.setText(
            f"Dönem toplamı: {_money(revenue)} — {count} satış, "
            f"ortalama sepet: {_money(revenue / count) if count else '—'}")
