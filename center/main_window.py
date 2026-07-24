"""Merkez yönetim arayüzü — ana pencere, sayfa gezinimi ve tema seçimi."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QShortcut, QStackedWidget, QVBoxLayout, QWidget,
)
from pymongo.errors import PyMongoError

from common import style
from common.font_scale_dialog import FontScaleDialog
from common.alerts import get_expiry_alerts, format_expiry_report
from common.settings import save_settings
from center.page_dashboard import DashboardPage
from center.page_products import ProductsPage
from center.page_craft import CraftPage
from center.page_stock import StockPage
from center.page_analytics import AnalyticsPage
from center.page_dealers import DealersPage
from center.page_dealer_stocks import DealerStocksPage
from center.page_dealer_stock_chart import DealerStockChartPage
from center.page_dealer_analytics import DealerAnalyticsPage
from center.page_reports import ReportsPage
from center.page_orders import OrdersPage
from common.expiry_chart import ExpiryChartWidget


class CenterWindow(QMainWindow):
    def __init__(self, db, settings: dict):
        super().__init__()
        self.db = db
        self.settings = settings
        self.setWindowTitle("GivorPartners — Merkez Yönetim")
        self.resize(1280, 800)
        self._build_ui()
        self._check_expiry_alerts()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---------------- Kenar çubuğu ----------------
        sidebar = QWidget(objectName="sidebar")
        sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 24, 14, 24)
        sidebar_layout.setSpacing(6)

        logo = QLabel("◈ GivorPartners")
        logo.setObjectName("logoText")
        subtitle = QLabel("Merkez Yönetim Paneli")
        subtitle.setObjectName("subtitle")
        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(28)

        self.pages = QStackedWidget()
        self._nav_buttons = []

        page_definitions = [
            ("📊  Genel Bakış", DashboardPage(self.db)),
            ("📦  Ürünler", ProductsPage(self.db)),
            ("🧩  Ürün Birleştir", CraftPage(self.db)),
            ("�📈  Stok Durumu", StockPage(self.db)),
            ("📉  Satış Analizi", AnalyticsPage(self.db)),            ("💰  Bayı Ciro Analizi", DealerAnalyticsPage(self.db)),            ("🏬  Bayiler", DealersPage(self.db)),
            ("📤  Bayi Stokları", DealerStocksPage(self.db)),            ("📊  Bayi Stok Grafikleri", DealerStockChartPage(self.db)),
            ("⚠  SKT Uyarıları", ExpiryChartWidget(self.db)),            ("📋  Siparişler", OrdersPage(self.db)),
            ("🧾  Satış Raporları", ReportsPage(self.db)),
        ]
        for index, (label, page) in enumerate(page_definitions):
            button = QPushButton(label, objectName="navButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _, i=index: self._open_page(i))
            sidebar_layout.addWidget(button)
            self._nav_buttons.append(button)
            self.pages.addWidget(page)

        sidebar_layout.addStretch()

        # Tema seçici
        theme_label = QLabel("Tema", objectName="cardTitle")
        self.theme_box = QComboBox()
        for key, theme in style.THEMES.items():
            self.theme_box.addItem(theme["display"], key)
        index = self.theme_box.findData(style.current_theme_name())
        if index >= 0:
            self.theme_box.setCurrentIndex(index)
        self.theme_box.currentIndexChanged.connect(self._change_theme)
        sidebar_layout.addWidget(theme_label)
        sidebar_layout.addWidget(self.theme_box)
        sidebar_layout.addSpacing(8)

        font_button = QPushButton("🔤  Yazı Boyutu",
                                  objectName="accentButton")
        font_button.setCursor(Qt.PointingHandCursor)
        font_button.clicked.connect(self._open_font_scale_dialog)
        sidebar_layout.addWidget(font_button)

        self.fullscreen_button = QPushButton("⛶  Tam Ekran (F11)",
                                             objectName="fullscreenButton")
        self.fullscreen_button.setCursor(Qt.PointingHandCursor)
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        sidebar_layout.addWidget(self.fullscreen_button)

        version = QLabel("v0.3.0")
        version.setObjectName("subtitle")
        sidebar_layout.addWidget(version)

        layout.addWidget(sidebar)
        
        # Bildirim göstergesi (üst-sağ köşe)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(16, 8, 16, 8)
        self.notification_badge = QLabel()
        self.notification_badge.setStyleSheet(
            "background-color: #ff4757; color: white; "
            "border-radius: 10px; padding: 2px 6px; font-weight: bold; font-size: 11px;"
        )
        self.notification_badge.setVisible(False)
        top_bar.addStretch()
        top_bar.addWidget(self.notification_badge)
        content_layout.addLayout(top_bar)
        content_layout.addWidget(self.pages, 1)
        layout.addWidget(content, 1)
        self._open_page(0)

        QShortcut(QKeySequence(Qt.Key_F11), self, self._toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._exit_fullscreen)

    def _change_theme(self):
        name = self.theme_box.currentData()
        style.set_theme(name)
        QApplication.instance().setStyleSheet(style.build_qss())
        self.settings["theme"] = name
        save_settings(self.settings)
        # Özel çizimli bileşenler (grafikler) yeni paletle yenilensin
        self._refresh_current_page()

    def _refresh_current_page(self):
        page = self.pages.currentWidget()
        if hasattr(page, "refresh"):
            try:
                page.refresh()
            except PyMongoError as error:
                QMessageBox.warning(
                    self, "Veritabanı Hatası",
                    f"Veriler yüklenemedi. Bağlantıyı kontrol edin.\n\n{error}")

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setText("⛶  Tam Ekran (F11)")
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("🗗  Pencere Modu (F11)")

    def _open_font_scale_dialog(self):
        """Yazı boyutu dialog'unu aç."""
        dialog = FontScaleDialog(self, self.settings)
        dialog.exec_()

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self._toggle_fullscreen()

    def _open_page(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self._nav_buttons):
            button.setChecked(i == index)
        page = self.pages.currentWidget()
        # Sayfa değişildiğinde bildirim göstergesini güncelle
        self._update_notification_badge()
        # Sayfanın refresh metodunu çalıştır
        self._refresh_current_page()
        style.fade_in_widget(page, duration_ms=300)
        self._refresh_current_page()

    def _update_notification_badge(self):
        """Bildirim göstergesini güncelle."""
        try:
            count = self.db.get_unread_notification_count()
            if count > 0:
                self.notification_badge.setText(str(count))
                self.notification_badge.setVisible(True)
            else:
                self.notification_badge.setVisible(False)
        except PyMongoError:
            pass

    def _check_expiry_alerts(self):
        """Başlangıçta SKT uyarılarını kontrol et."""
        try:
            alerts = get_expiry_alerts(self.db, warning_days=30)
            
            if alerts["expired"] or alerts["expiring_soon"]:
                report = format_expiry_report(alerts)
                QMessageBox.warning(
                    self, "⚠️  SKT UYARISI",
                    report + "\n\nDetaylar için Ürünler sayfasını kontrol edin.")
        except PyMongoError:
            pass
