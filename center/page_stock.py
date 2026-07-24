"""Stok durumu sayfası — ürün stoklarını yatay çubuk grafikle gösterir.

Grafik harici kütüphane gerektirmez; QPainter ile çizilir.
Renk kodu: kırmızı = kritik, sarı = az, turkuaz = yeterli.
Bayi dropdown'ı ile bayi bazlı stok görüntülenebilir.
"""
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from common import style

ROW_HEIGHT = 34
LABEL_WIDTH = 220


class StockChart(QWidget):
    """Ürün stoklarını yatay çubuklarla çizen özel bileşen."""

    def __init__(self):
        super().__init__()
        self._products = []      # [(name, stock), ...]
        self._critical_threshold = 10
        self._low_threshold = 30

    def set_data(self, products: list, critical: int, low: int):
        self._products = products
        self._critical_threshold = critical
        self._low_threshold = low
        self.setMinimumHeight(max(len(products), 1) * ROW_HEIGHT + 20)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pal = style.palette()

        if not self._products:
            painter.setPen(QColor(pal["muted"]))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "Gösterilecek ürün bulunamadı.")
            return

        highest = max(max(s for _, s in self._products), 1)
        bar_area = self.width() - LABEL_WIDTH - 70

        font = QFont(self.font())
        font.setPointSize(10)
        painter.setFont(font)

        for i, (name, stock) in enumerate(self._products):
            y = 10 + i * ROW_HEIGHT

            # Ürün adı
            painter.setPen(QColor(pal["text"]))
            painter.drawText(
                QRectF(0, y, LABEL_WIDTH - 12, ROW_HEIGHT - 10),
                Qt.AlignRight | Qt.AlignVCenter,
                name if len(name) <= 28 else name[:27] + "…",
            )

            # Arka plan izi
            track = QRectF(LABEL_WIDTH, y + 4, bar_area, ROW_HEIGHT - 14)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(pal["card"]))
            painter.drawRoundedRect(track, 6, 6)

            # Stok çubuğu
            ratio = max(stock, 0) / highest
            if stock <= self._critical_threshold:
                color = QColor(pal["red"])
            elif stock <= self._low_threshold:
                color = QColor(pal["yellow"])
            else:
                color = QColor(pal["accent"])
            width = max(bar_area * ratio, 4 if stock > 0 else 0)
            if width:
                bar = QRectF(LABEL_WIDTH, y + 4, width, ROW_HEIGHT - 14)
                painter.setBrush(color)
                painter.drawRoundedRect(bar, 6, 6)

            # Stok değeri
            painter.setPen(color if stock <= self._low_threshold
                           else QColor(pal["text"]))
            painter.drawText(
                QRectF(LABEL_WIDTH + bar_area + 8, y, 56, ROW_HEIGHT - 10),
                Qt.AlignLeft | Qt.AlignVCenter,
                str(stock),
            )


def _badge(text: str) -> QLabel:
    return QLabel(text)


def _style_badge(label: QLabel, color: str):
    label.setStyleSheet(
        f"color: {color}; font-size: 12px; font-weight: 600;"
        f"border: 1px solid {style.palette()['border']}; border-radius: 8px;"
        "padding: 4px 10px;"
    )


class StockPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top = QHBoxLayout()
        title = QLabel("Stok Durumu", objectName="title")
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Ürün ara…")
        self.search.setFixedWidth(220)
        self.search.textChanged.connect(self.refresh)
        # Bayi seçici
        self.dealer_combo = QComboBox()
        self.dealer_combo.setMinimumWidth(180)
        self.dealer_combo.addItem("📦 Genel Depo", "")
        self.dealer_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(QLabel("Depo:", objectName="subtitle"))
        top.addWidget(self.dealer_combo)
        top.addWidget(self.search)
        layout.addLayout(top)

        # Eşik ayarları + açıklama rozetleri
        options = QHBoxLayout()
        options.setSpacing(10)
        options.addWidget(QLabel("Kritik eşik:", objectName="subtitle"))
        self.critical_threshold = QSpinBox(minimum=0, maximum=100000)
        self.critical_threshold.setValue(10)
        self.critical_threshold.valueChanged.connect(self.refresh)
        options.addWidget(self.critical_threshold)
        options.addWidget(QLabel("Az stok eşiği:", objectName="subtitle"))
        self.low_threshold = QSpinBox(minimum=0, maximum=100000)
        self.low_threshold.setValue(30)
        self.low_threshold.valueChanged.connect(self.refresh)
        options.addWidget(self.low_threshold)
        options.addStretch()
        self.badge_critical = _badge("● Kritik")
        self.badge_low = _badge("● Az")
        self.badge_ok = _badge("● Yeterli")
        options.addWidget(self.badge_critical)
        options.addWidget(self.badge_low)
        options.addWidget(self.badge_ok)
        layout.addLayout(options)

        self.summary_label = QLabel("", objectName="subtitle")
        layout.addWidget(self.summary_label)

        self.chart = StockChart()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.chart)
        layout.addWidget(scroll, 1)

    def refresh(self):
        pal = style.palette()
        _style_badge(self.badge_critical, pal["red"])
        _style_badge(self.badge_low, pal["yellow"])
        _style_badge(self.badge_ok, pal["accent"])

        # Bayileri combo'ya yükle (ilk açılışta)
        if self.dealer_combo.count() == 1:
            try:
                for dealer in self.db.get_dealers():
                    self.dealer_combo.addItem(
                        f"🏬 {dealer['name']}", dealer["code"])
            except Exception:
                pass

        dealer_code = self.dealer_combo.currentData()
        search = self.search.text().strip()

        if dealer_code:
            # Bayi deposu
            stocks = self.db.get_all_dealer_stocks(dealer_code)
            if search:
                import re
                safe = re.escape(search[:100])
                stocks = [s for s in stocks
                          if re.search(safe, s.get("name", ""), re.I)
                          or re.search(safe, s.get("barcode", ""))]
            data = sorted(
                ((s.get("name", s.get("barcode", "?")),
                  int(s.get("stock", 0)))
                 for s in stocks),
                key=lambda pair: pair[1],
            )
        else:
            # Genel depo
            products = self.db.get_products(search)
            data = sorted(
                ((p.get("name", "?"), int(p.get("stock", 0)))
                 for p in products),
                key=lambda pair: pair[1],
            )

        critical = self.critical_threshold.value()
        low = self.low_threshold.value()
        self.chart.set_data(data, critical, low)

        critical_count = sum(1 for _, s in data if s <= critical)
        low_count = sum(1 for _, s in data if critical < s <= low)
        self.summary_label.setText(
            f"{len(data)} ürün listelendi — "
            f"{critical_count} kritik, {low_count} az stokta. "
            "Çubuklar en düşük stoktan yükseğe sıralıdır."
        )
