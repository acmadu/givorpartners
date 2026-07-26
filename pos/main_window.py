"""Kasa (POS) arayüzü.

Barkod okuma:
- USB barkod okuyucular (masaüstü sabit modeller dahil) klavye gibi
  davranır: barkodu yazıp Enter (veya Tab) basar.
- Uygulama genelinde tuş yakalama vardır: odak sepette ya da bir butonda
  olsa bile okutulan barkod otomatik olarak barkod kutusuna yönlenir.
  Böylece masaya sabit okuyucuyla okutma hiçbir zaman kaybolmaz.
- Koli barkodu okutulursa koli içi adet kadar ürün sepete eklenir.
- Kamera desteği kuruluysa "📷 Kamera" butonu ile karekod okunabilir.
"""
import os
from datetime import datetime

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QShortcut, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from common import style
from common.font_scale_dialog import FontScaleDialog
from common.alerts import get_expiry_alerts, format_expiry_report
from common.settings import save_settings
from pos.barcode_camera import CAMERA_SUPPORT, CameraReader
from pos.payment_terminal import PaymentTerminal
from pos.payment_dialog import CardPaymentDialog
from pos.order_dialog import OrderDialog
from pos.order_return_dialog import OrderReturnDialog
from pos.return_dialog import ReturnDialog
from pos.dealer_stock_dialog import DealerStockDialog
from pos.dealer_stock_dashboard import DealerStockDashboard
from pos.dealer_analytics_dialog import DealerAnalyticsDialog
from pos.pending_stock_approval import PendingStockApprovalDialog
from pos.customer_info_dialog import CustomerInfoDialog
from pos.end_of_day_report import EndOfDayReportDialog
from pos.shortcut_products_dialog import ShortcutProductDialog
from pymongo.errors import PyMongoError


class PosWindow(QMainWindow):
    def __init__(self, db, dealer: dict, settings: dict = None):
        super().__init__()
        self.db = db
        self.dealer = dealer
        self.settings = settings or {}
        self.cart = {}  # barcode -> {ürün bilgileri, adet}
        self.camera = None
        self._terminal = PaymentTerminal(self.settings)
        self.setWindowTitle(
            f"GivorPartners — {dealer['name']} ({dealer['code']})")
        # Favicon ayarla
        favicon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'favicon.ico')
        if os.path.exists(favicon_path):
            self.setWindowIcon(QIcon(favicon_path))
        # Minimum boyut ayarla (responsive design için)
        self.setMinimumSize(1024, 600)
        self._build_ui()
        self._start_clock()
        # Sabit okuyucu desteği: tüm tuş vuruşlarını izle (bkz. eventFilter)
        QApplication.instance().installEventFilter(self)
        self.barcode_input.installEventFilter(self)
        # SKT uyarılarını göster
        self._check_expiry_alerts()

    def eventFilter(self, obj, event):
        """Masaüstü sabit okuyucu entegrasyonu.

        1) Okuyucu Tab soneki gönderecek şekilde ayarlıysa Tab'ı Enter
           gibi işle (odak başka bileşene kaçmasın).
        2) Odak sepette/butondayken gelen yazılabilir karakterleri barkod
           kutusuna yönlendir — okutma asla kaybolmaz.
        """
        if event.type() == QEvent.KeyPress:
            if obj is self.barcode_input:
                if (event.key() == Qt.Key_Tab
                        and self.barcode_input.text().strip()):
                    self._barcode_scanned()
                    return True
                return False
            if (QApplication.activeModalWidget() is None
                    and not self.barcode_input.hasFocus()
                    and not event.modifiers() & (Qt.ControlModifier
                                                 | Qt.AltModifier)):
                text = event.text()
                if text and text.isprintable() and not text.isspace():
                    self.barcode_input.setFocus()
                    self.barcode_input.insert(text)
                    return True
                if (event.key() in (Qt.Key_Return, Qt.Key_Enter)
                        and self.barcode_input.text().strip()):
                    self._barcode_scanned()
                    return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------ Arayüz
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.setSpacing(14)

        # Üst bilgi çubuğu
        top = QHBoxLayout()
        dealer_label = QLabel(f"🏬  {self.dealer['name']}",
                              objectName="title")
        self.clock_label = QLabel("", objectName="subtitle")
        self.fullscreen_button = QPushButton("⛶", objectName="fullscreenButton")
        self.fullscreen_button.setToolTip("Tam ekran (F11)")
        self.fullscreen_button.setCursor(Qt.PointingHandCursor)
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        top.addWidget(dealer_label)
        top.addStretch()
        top.addWidget(self.clock_label)
        # Tema değiştirici
        self.theme_button = QPushButton("🎨")
        self.theme_button.setFixedSize(36, 36)
        self.theme_button.setToolTip("Tema değiştir")
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.clicked.connect(self._cycle_theme)
        top.addWidget(self.theme_button)
        top.addWidget(self.fullscreen_button)
        outer.addLayout(top)

        QShortcut(QKeySequence(Qt.Key_F11), self, self._toggle_fullscreen)

        body = QHBoxLayout()
        body.setSpacing(16)
        outer.addLayout(body, 1)

        # ---------------- Sol: barkod + sepet ----------------
        left = QVBoxLayout()
        left.setSpacing(12)

        # Müşteri bilgileri sadece ödeme anında alınır (instance vars)
        self._customer_data = {}

        barcode_row = QHBoxLayout()
        self.barcode_input = QLineEdit(objectName="barcodeInput")
        self.barcode_input.setPlaceholderText(
            "Barkod okutun veya yazıp Enter'a basın…")
        self.barcode_input.returnPressed.connect(self._barcode_scanned)
        barcode_row.addWidget(self.barcode_input, 1)
        # Kamera butonu her zaman görünür; destek yoksa sarı uyarı tooltip'i
        self.camera_button = QPushButton("📷 Kamera")
        self.camera_button.setCheckable(True)
        if CAMERA_SUPPORT:
            self.camera_button.setToolTip("Kamerayla barkod/karekod oku")
            self.camera_button.toggled.connect(self._toggle_camera)
        else:
            self.camera_button.setToolTip(
                "Kamera desteği aktif değil.\n"
                "Kurmak için: pip install opencv-python pyzbar")
            self.camera_button.setEnabled(False)
        barcode_row.addWidget(self.camera_button)
        left.addLayout(barcode_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün", "Adet", "Birim Fiyat", "Tutar"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        left.addWidget(self.table, 1)

        cart_buttons = QHBoxLayout()
        increase = QPushButton("＋ Adet")
        increase.clicked.connect(lambda: self._change_quantity(1))
        decrease = QPushButton("－ Adet")
        decrease.clicked.connect(lambda: self._change_quantity(-1))
        remove = QPushButton("🗑 Satırı Kaldır")
        remove.clicked.connect(self._remove_row)
        cart_buttons.addWidget(increase)
        cart_buttons.addWidget(decrease)
        cart_buttons.addWidget(remove)
        cart_buttons.addStretch()
        left.addLayout(cart_buttons)

        body.addLayout(left, 2)

        # ---------------- Sağ: toplam + ödeme ----------------
        right_panel = QWidget(objectName="card")
        right = QVBoxLayout(right_panel)
        right.setContentsMargins(16, 16, 16, 16)
        right.setSpacing(12)

        right.addWidget(QLabel("GENEL TOPLAM", objectName="cardTitle"))
        self.total_label = QLabel("0,00 ₺", objectName="totalAmount")
        right.addWidget(self.total_label)

        self.last_product_label = QLabel("", objectName="subtitle")
        self.last_product_label.setWordWrap(True)
        right.addWidget(self.last_product_label)
        right.addStretch()

        # ──── Ödeme butonları (Ana işlemler) ────
        cash = QPushButton("💵  NAKİT", objectName="success")
        cash.clicked.connect(self._payment_with_customer_info("NAKİT"))
        card = QPushButton("💳  KREDİ KARTI", objectName="primary")

        card.clicked.connect(self._payment_with_customer_info("KART"))

        # ──── Kısayol Ürünleri ────
        shortcut_btn = QPushButton("⭐  Kısayol Ürünleri", objectName="secondary")
        shortcut_btn.clicked.connect(self._manage_shortcuts)

        # ──── Sipariş & Depo ────
        order_btn = QPushButton("📋  Sipariş Ver", objectName="secondary")
        order_btn.clicked.connect(self._open_order_dialog)
        receive_order_btn = QPushButton("✓  Sipariş Teslim Al", objectName="secondary")
        receive_order_btn.clicked.connect(self._receive_order)
        stock_btn = QPushButton("📦  Depo", objectName="secondary")
        stock_btn.clicked.connect(self._open_stock_dialog)
        pending_approval_btn = QPushButton("✓  Depo Onayları", objectName="secondary")
        pending_approval_btn.clicked.connect(self._open_pending_approval)

        # ──── Raporlar ────
        expiry_warn_btn = QPushButton("⚠  SKT Uyarıları", objectName="secondary")
        expiry_warn_btn.clicked.connect(self._open_expiry_chart)
        analytics_btn = QPushButton("📊  Ciro Raporu", objectName="secondary")
        analytics_btn.clicked.connect(self._open_analytics)
        eod_report_btn = QPushButton("📊  Gün Sonu Raporu", objectName="secondary")
        eod_report_btn.clicked.connect(self._open_eod_report)

        # ──── İadeler ────
        order_return_btn = QPushButton("↩  Sipariş İadesi", objectName="secondary")
        order_return_btn.clicked.connect(self._open_order_return_dialog)
        refund_btn = QPushButton("🔄  Müşteri İadesi", objectName="secondary")
        refund_btn.clicked.connect(self._open_return_dialog)

        # ──── İptal ────
        cancel_btn = QPushButton("✖  SATIŞI İPTAL ET", objectName="danger")
        cancel_btn.clicked.connect(self._clear_cart)

        # ──── POS Ayarları ────
        pos_settings_btn = QPushButton("⚙  POS Terminal Ayarları", objectName="secondary")

        pos_settings_btn.clicked.connect(self._open_pos_settings)

        # ──────── PANEL LAYOUT ────────
        # 1. Ödeme (üst) - FULL WIDTH
        right.addWidget(cash)
        right.addWidget(card)
        right.addSpacing(12)

        # 2-5. Tüm işlem butonları ScrollArea'da 2-COLUMN GRID
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        buttons_container = QWidget()
        buttons_grid = QGridLayout(buttons_container)
        buttons_grid.setContentsMargins(0, 0, 0, 0)
        buttons_grid.setSpacing(10)
        buttons_grid.setColumnStretch(0, 1)
        buttons_grid.setColumnStretch(1, 1)
        
        row = 0
        
        # 2. Kısayol Ürünleri
        buttons_grid.addWidget(QLabel("HIZLI ERİŞİM", objectName="cardTitle"), row, 0, 1, 2)
        row += 1
        
        shortcuts_panel = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_panel)
        shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_layout.setSpacing(8)
        self.shortcuts_buttons = []
        self._load_and_display_shortcuts(shortcuts_layout)
        shortcuts_layout.addStretch()
        buttons_grid.addWidget(shortcuts_panel, row, 0, 1, 2)
        row += 1
        buttons_grid.addWidget(shortcut_btn, row, 0, 1, 2)
        row += 1
        
        # 3. İşlemler
        buttons_grid.addWidget(QLabel("İŞLEMLER", objectName="cardTitle"), row, 0, 1, 2)
        row += 1
        buttons_grid.addWidget(order_btn, row, 0)
        buttons_grid.addWidget(receive_order_btn, row, 1)
        row += 1
        buttons_grid.addWidget(stock_btn, row, 0)
        buttons_grid.addWidget(pending_approval_btn, row, 1)
        row += 1
        
        # 4. Raporlar
        buttons_grid.addWidget(QLabel("RAPORLAR", objectName="cardTitle"), row, 0, 1, 2)
        row += 1
        buttons_grid.addWidget(expiry_warn_btn, row, 0)
        buttons_grid.addWidget(analytics_btn, row, 1)
        row += 1
        buttons_grid.addWidget(eod_report_btn, row, 0, 1, 2)
        row += 1
        
        # 5. İade & İptal
        buttons_grid.addWidget(QLabel("İADE & İPTAL", objectName="cardTitle"), row, 0, 1, 2)
        row += 1
        buttons_grid.addWidget(order_return_btn, row, 0)
        buttons_grid.addWidget(refund_btn, row, 1)
        row += 1
        buttons_grid.addWidget(pos_settings_btn, row, 0, 1, 2)
        row += 1
        buttons_grid.addWidget(cancel_btn, row, 0, 1, 2)
        row += 1
        buttons_grid.setRowStretch(row, 1)
        
        scroll.setWidget(buttons_container)
        right.addWidget(scroll)

        body.addWidget(right_panel, 1)
        self.barcode_input.setFocus()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setText("⛶")
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("🗗")
        self.barcode_input.setFocus()

    def _cycle_theme(self):
        """Temalar arasında döngüsel geçiş yapar ve kaydeder."""
        themes = list(style.THEMES.keys())
        current = self.settings.get("theme", style.current_theme_name())
        if current in themes:
            idx = (themes.index(current) + 1) % len(themes)
        else:
            idx = 0
        new_theme = themes[idx]
        self.settings["theme"] = new_theme
        save_settings(self.settings)
        style.set_theme(new_theme)
        QApplication.instance().setStyleSheet(style.build_qss())
        self.barcode_input.setFocus()

    def _start_clock(self):
        timer = QTimer(self)
        timer.timeout.connect(
            lambda: self.clock_label.setText(
                datetime.now().strftime("%d.%m.%Y  %H:%M:%S")))
        timer.start(1000)

    # ------------------------------------------------------------- Barkod
    def _barcode_scanned(self, barcode: str = ""):
        barcode = (barcode or self.barcode_input.text()).strip()
        self.barcode_input.clear()
        self.barcode_input.setFocus()
        if not barcode:
            return

        try:
            product, multiplier = self.db.find_product_by_barcode(barcode)
        except PyMongoError:
            self._show_info("⚠ Veritabanına ulaşılamıyor — bağlantıyı "
                            "kontrol edin.", style.palette()["red"])
            return
        if not product:
            self._show_info(f"⚠ '{barcode}' için ürün bulunamadı!",
                            style.palette()["red"])
            return

        # Bayi stoğunu kontrol et (sadece bayi deposundaki ürünler satılabilir)
        dealer_stock = self.db.get_dealer_stock(
            self.dealer.get("code", ""), product["barcode"])
        
        # Depoda olmayan ürün satılamaz — sepete EKLEMEDen kontrol et!
        if dealer_stock is None or dealer_stock <= 0:
            self._show_info(
                f"⚠ {product['name']} deponuza alınmamış!",
                style.palette()["red"])
            return
        
        stock = dealer_stock
        
        key = product["barcode"]
        if key in self.cart:
            self.cart[key]["quantity"] += multiplier
        else:
            self.cart[key] = {
                "barcode": key,
                "name": product["name"],
                "price": float(product.get("price", 0)),
                "quantity": multiplier,
            }
        box_note = f" (koli ×{multiplier})" if multiplier > 1 else ""
        
        # Birim bilgisi
        unit = product.get("unit", "adet")
        
        # SKT uyarısı
        from datetime import datetime, timedelta, date
        expiry = product.get("expiry_date")
        if isinstance(expiry, datetime):
            expiry = expiry.date()
        warning_text = ""
        if expiry:
            days_left = (expiry - date.today()).days
            if days_left < 0:
                warning_text = f" ⚠ SKT GEÇMİŞ ({expiry.strftime('%d.%m.%Y')})"
            elif days_left <= 30:
                warning_text = f" ⚠ SKT YAKLAŞIYOR ({expiry.strftime('%d.%m.%Y')})"
        
        if stock < self.cart[key]["quantity"]:
            self._show_info(
                f"⚠ {product['name']} ({unit}){box_note}{warning_text} — stok yetersiz! "
                f"(kalan: {stock})", style.palette()["red"])
        else:
            self._show_info(
                f"✔ {product['name']} ({unit}){box_note}{warning_text} — "
                f"{product.get('price', 0):.2f} ₺  |  stok: {stock}",
                style.palette()["muted"])
        self._render_cart()

    def _toggle_camera(self, enabled: bool):
        if enabled:
            self.camera = CameraReader()
            self.camera.barcode_read.connect(self._barcode_scanned)
            self.camera.error.connect(self._camera_error)
            self.camera.start()
            self._show_info("📷 Kamera açık — karekodu gösterin",
                            style.palette()["yellow"])
        elif self.camera:
            self.camera.stop()
            self.camera = None

    def _camera_error(self, message: str):
        QMessageBox.warning(self, "Kamera", message)
        # Buton basılı kalmasın; toggled(False) kamerayı da kapatır
        self.camera_button.setChecked(False)

    # -------------------------------------------------------------- Sepet
    def _render_cart(self):
        self.table.setRowCount(len(self.cart))
        total = 0.0
        for row, item in enumerate(self.cart.values()):
            amount = item["quantity"] * item["price"]
            total += amount
            cells = [
                item["barcode"], item["name"], str(item["quantity"]),
                f"{item['price']:.2f} ₺", f"{amount:.2f} ₺",
            ]
            for column, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                if column >= 2:
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, column, cell)
        self.total_label.setText(
            f"{total:,.2f} ₺".replace(",", "X").replace(".", ",")
            .replace("X", "."))

    def _selected_key(self) -> str:
        row = self.table.currentRow()
        return self.table.item(row, 0).text() if row >= 0 else ""

    def _change_quantity(self, delta: int):
        key = self._selected_key()
        if not key or key not in self.cart:
            return
        self.cart[key]["quantity"] += delta
        if self.cart[key]["quantity"] <= 0:
            del self.cart[key]
        self._render_cart()
        self.barcode_input.setFocus()

    def _remove_row(self):
        key = self._selected_key()
        if key and key in self.cart:
            del self.cart[key]
            self._render_cart()
        self.barcode_input.setFocus()

    def _clear_cart(self):
        self.cart.clear()
        self._customer_data = {}
        self._render_cart()
        self._show_info("", style.palette()["muted"])
        self.barcode_input.setFocus()

    def _open_pos_settings(self):
        from pos.pos_settings_dialog import PosSettingsDialog
        dlg = PosSettingsDialog(self)
        if dlg.exec_():
            # Ayarlar kaydedildi — terminal nesnesini yenile
            from common.settings import load_settings
            from pos.payment_terminal import PaymentTerminal
            self.settings = load_settings()
            self._terminal = PaymentTerminal(self.settings)
            mode = self.settings.get("terminal_mode", "manual")
            self._show_info(f"POS modu güncellendi: {mode}", style.palette()["green"])

    # -------------------------------------------------------------- Satış
    def _payment_with_customer_info(self, payment_type: str):
        """Müşteri bilgisi alıp ödemeyi başlat (müşteri girişi isteğe bağlı)."""
        def _do():
            if not self.cart:
                QMessageBox.information(self, "Sepet Boş", "Önce ürün okutun.")
                return
            dialog = CustomerInfoDialog(self)
            result = dialog.exec_()
            if result == QDialog.Rejected:
                # "Atla" butonu da Rejected döndürür — müşteri verisi boş bırakılır
                pass
            self._customer_data = dialog.get_data()
            if payment_type == "KART":
                self._initiate_card_payment()
            else:
                self._complete_sale(payment_type)
        return _do

    def _initiate_card_payment(self):
        """KREDİ KARTI ödemeyi başlat."""
        if not self.cart:
            QMessageBox.information(self, "Sepet Boş", "Önce ürün okutun.")
            return
        total = sum(i["quantity"] * i["price"] for i in self.cart.values())
        dialog = CardPaymentDialog(self, self._terminal, total)
        if dialog.exec_() == CardPaymentDialog.Accepted and dialog.result:
            payment_result = dialog.result
            extra = {}
            if payment_result.auth_code:
                extra["auth_code"] = payment_result.auth_code
            if payment_result.ref_no:
                extra["terminal_ref"] = payment_result.ref_no
            self._complete_sale("KART", extra)
        else:
            self._show_info("Kart ödemesi iptal edildi.",
                            style.palette()["yellow"])
            self.barcode_input.setFocus()

    def _complete_sale(self, payment_type: str, extra: dict = None):
        """Satışı kaydet."""
        if not self.cart:
            return
        total = sum(i["quantity"] * i["price"] for i in self.cart.values())
        cd = self._customer_data
        sale = {
            "dealer_code": self.dealer["code"],
            "customer_name": cd.get("name") or "İsimsiz",
            "customer_surname": cd.get("surname") or "",
            "customer_phone": cd.get("phone") or "",
            "customer_birthdate": cd.get("birthdate") or "",
            "customer_anniversary": cd.get("anniversary") or "",
            "date": datetime.now(),
            "payment_type": payment_type,
            "total": round(total, 2),
            "items": [
                {
                    "barcode": i["barcode"],
                    "name": i["name"],
                    "quantity": i["quantity"],
                    "unit_price": i["price"],
                }
                for i in self.cart.values()
            ],
        }
        if extra:
            sale.update(extra)
        try:
            self.db.save_sale(sale)
        except PyMongoError as error:
            QMessageBox.critical(
                self, "Kayıt Hatası",
                f"Satış kaydedilemedi — sepet korunuyor, tekrar deneyin.\n\n{error}")
            return
        details = f"Ödeme: {payment_type}\nToplam: {total:.2f} ₺"
        if extra and extra.get("auth_code"):
            details += f"\nOnay Kodu: {extra['auth_code']}"
        if extra and extra.get("terminal_ref"):
            details += f"\nRef No: {extra['terminal_ref']}"
        QMessageBox.information(self, "✓ Satış Tamamlandı", details)
        self._clear_cart()

    def _show_info(self, text: str, color: str):
        self.last_product_label.setText(text)
        self.last_product_label.setStyleSheet(
            f"color: {color}; font-size: 15px;")

    def _open_order_dialog(self):
        """Sipariş oluşturma dialogunu aç."""
        dialog = OrderDialog(self, self.db, self.dealer)
        if dialog.exec_() == QDialog.Accepted:
            try:
                order_data = dialog.order_data
                
                # Dekont dosyasını kopyala ve path'i güncelle
                dekont_url = None
                if order_data.get("dekont_file"):
                    import shutil
                    from pathlib import Path
                    dekont_dir = Path("./dekonts")
                    dekont_dir.mkdir(exist_ok=True)
                    src = order_data["dekont_file"]
                    filename = Path(src).name
                    dest = dekont_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    shutil.copy2(src, dest)
                    dekont_url = str(dest)
                    order_data["dekont_url"] = dekont_url
                    del order_data["dekont_file"]
                
                order_id = self.db.create_order(order_data)
                
                # Bildirim oluştur (merkezde gösterilir)
                self.db.create_notification({
                    "type": "order_new",
                    "order_id": order_id,
                    "dealer_code": self.dealer["code"],
                    "dealer_name": self.dealer["name"],
                    "total": order_data["total"],
                    "item_count": len(order_data["items"]),
                })
                QMessageBox.information(
                    self, "✓ Sipariş Gönderildi",
                    f"Sipariş ID: {order_id}\n"
                    f"Toplam: {order_data['total']:.2f} ₺\n\n"
                    "Merkezde onay bekleniyor.")
                self.barcode_input.setFocus()
            except PyMongoError as error:
                QMessageBox.critical(
                    self, "Hata", f"Sipariş gönderilemedi:\n{error}")

    def _receive_order(self):
        """Merkezde onaylanmış siparişi al ve stoğa ekle."""
        try:
            # Merkezde onaylandı veya gönderildi siparişleri bul
            orders = list(self.db.orders.find({
                "dealer_code": self.dealer["code"],
                "status": {"$in": ["confirmed", "shipped"]}
            }).sort("created_at", -1))

            if not orders:
                QMessageBox.information(self, "Siparişler", "Beklemede sipariş yok.")
                return

            # Sipariş seçim listesi
            dialog = QDialog(self)
            dialog.setWindowTitle("Sipariş Al")
            dialog.setMinimumSize(500, 300)

            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Sipariş seçin:"))

            table = QTableWidget(len(orders), 4)
            table.setHorizontalHeaderLabels(["Tarih", "Durum", "Toplam", "Kalem"])
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.NoEditTriggers)

            for row, order in enumerate(orders):
                date_text = order.get("created_at").strftime("%d.%m.%Y %H:%M") if order.get("created_at") else "?"
                status_text = {"confirmed": "Onaylandı", "shipped": "Gönderildi"}.get(order.get("status"), order.get("status"))
                total_text = f"{order.get('total', 0):.2f} ₺"
                count_text = str(len(order.get("items", [])))

                for col, text in enumerate([date_text, status_text, total_text, count_text]):
                    item = QTableWidgetItem(text)
                    table.setItem(row, col, item)

                table.item(row, 0).setData(Qt.UserRole, order["_id"])

            table.selectRow(0)
            layout.addWidget(table)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.button(QDialogButtonBox.Ok).setText("Sipariş Alındı ✓")
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec_() != QDialog.Accepted:
                return

            # Seçilen sipariş
            row = table.currentRow()
            if row < 0:
                return

            selected_order = orders[row]
            order_id = selected_order["_id"]
            dealer_code = selected_order["dealer_code"]

            # Durumu "delivered" yap → stok otomatik eklenir
            self.db.update_order_status(order_id, "delivered")

            # Manuel olarak stoğa ekle (veritabanında çift eklemesi olmasın diye)
            for item in selected_order.get("items", []):
                barcode = item['barcode']
                qty = item['quantity_boxes'] * item.get('unit_quantity', 1)
                self.db.dealer_stocks.update_one(
                    {"dealer_code": dealer_code, "barcode": barcode},
                    {"$inc": {"stock": qty}},
                    upsert=True)

            QMessageBox.information(
                self, "✓ Sipariş Alındı",
                f"Sipariş alındı.\n"
                f"{len(selected_order.get('items', []))} kalem stoğa eklendi.")

        except PyMongoError as error:
            QMessageBox.critical(self, "Hata", f"Hata:\n{error}")

    def _open_stock_dialog(self):
        """Bayi depo stok dashboard'ını aç."""
        dashboard = DealerStockDashboard(self, self.db, self.dealer["code"], self.dealer["name"])
        dashboard.exec_()

    def _open_pending_approval(self):
        """Merkez'den gelen beklemede stokları onayla."""
        dialog = PendingStockApprovalDialog(self, self.db, self.dealer["code"], self.dealer["name"])
        dialog.exec_()

    def _open_expiry_chart(self):
        """SKT uyarı grafiğini göster."""
        from common.expiry_chart import ExpiryChartWidget
        dlg = QDialog(self)
        dlg.setWindowTitle("⚠ Son Kullanım Tarihi Uyarıları")
        dlg.setMinimumSize(900, 600)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = ExpiryChartWidget(self.db, dealer_code=self.dealer["code"], parent=dlg)
        layout.addWidget(widget)
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec_()

    def _open_analytics(self):
        """Bayı ciro analitiklerini göster."""
        dlg = DealerAnalyticsDialog(self, self.db, self.dealer["code"])
        dlg.exec_()

    def _open_font_scale_dialog(self):
        """Yazı boyutu dialog'unu aç."""
        dialog = FontScaleDialog(self, self.settings)
        dialog.exec_()

    def _open_return_dialog(self):
        """Müşteri iade talebi oluşturma dialogunu aç."""
        if not self.cart:
            QMessageBox.information(self, "İade", "Sepete ürün ekleyin.")
            return
        dialog = ReturnDialog(self, self.db, self.dealer, self.cart)
        if dialog.exec_() == QDialog.Accepted:
            try:
                return_id = self.db.create_return(dialog.return_data)
                # Bildirim oluştur
                self.db.create_notification({
                    "type": "return_new",
                    "return_id": return_id,
                    "dealer_code": self.dealer["code"],
                    "dealer_name": self.dealer["name"],
                    "item_count": len(dialog.return_data["items"]),
                })
                QMessageBox.information(
                    self, "✓ İade Talebi Gönderildi",
                    f"İade ID: {return_id}\n\n"
                    "Merkezde inceleme bekleniyor.")
                self.barcode_input.setFocus()
            except PyMongoError as error:
                QMessageBox.critical(
                    self, "Hata", f"İade talebi gönderilemedi:\n{error}")

    def _open_order_return_dialog(self):
        """Sipariş iade talebi oluşturma dialogunu aç."""
        dialog = OrderReturnDialog(self, self.db, self.dealer)
        if dialog.exec_() == QDialog.Accepted:
            try:
                return_id = self.db.create_return(dialog.return_data)
                # Bildirim oluştur
                self.db.create_notification({
                    "type": "order_return_new",
                    "return_id": return_id,
                    "order_id": dialog.return_data.get("order_id"),
                    "dealer_code": self.dealer["code"],
                    "dealer_name": self.dealer["name"],
                    "item_count": len(dialog.return_data["items"]),
                })
                QMessageBox.information(
                    self, "✓ Sipariş İade Talebi Gönderildi",
                    f"İade ID: {return_id}\n\n"
                    "Merkezde inceleme bekleniyor.")
                self.barcode_input.setFocus()
            except PyMongoError as error:
                QMessageBox.critical(
                    self, "Hata", f"Sipariş iade talebi gönderilemedi:\n{error}")

    def _check_expiry_alerts(self):
        """Başlangıçta SKT uyarılarını kontrol et."""
        try:
            alerts = get_expiry_alerts(self.db, warning_days=30)
            
            if alerts["expired"] or alerts["expiring_soon"]:
                report = format_expiry_report(alerts)
                QMessageBox.warning(
                    self, "⚠️  SKT UYARISI",
                    report + "\n\nBu ürünleri satmayın!")
        except PyMongoError:
            pass

    def _load_and_display_shortcuts(self, layout):
        """Kısayol ürünleri yükle ve göster."""
        try:
            dealer = self.db.dealers.find_one({"code": self.dealer["code"]})
            shortcuts = dealer.get("shortcut_products", []) if dealer else []
            
            # Sıraya göre sort et
            shortcuts = sorted(shortcuts, key=lambda x: x.get("order", 999))
            
            for shortcut in shortcuts[:8]:  # Max 8 kısayol
                barcode = shortcut.get("barcode", "")
                product = self.db["products"].find_one({"barcode": barcode})
                
                if not product:
                    continue
                
                btn = QPushButton(f"⭐ {product['name'][:15]}")
                btn.setMinimumHeight(36)
                btn.setObjectName("secondary")
                btn.clicked.connect(
                    lambda _, bc=barcode: self._barcode_scanned(bc)
                )
                layout.addWidget(btn)
                self.shortcuts_buttons.append(btn)
                
        except PyMongoError:
            pass

    def _manage_shortcuts(self):
        """Kısayol ürünleri yönetim diyalogunu aç."""
        dialog = ShortcutProductDialog(
            self.db, self.dealer["code"], self
        )
        if dialog.exec_() == QDialog.Accepted:
            # Kısayolları yeniden yükle
            for btn in self.shortcuts_buttons:
                btn.setParent(None)
            self.shortcuts_buttons.clear()
            
            # Yeni panel oluştur
            shortcuts_panel = QWidget()
            shortcuts_layout = QVBoxLayout(shortcuts_panel)
            shortcuts_layout.setContentsMargins(0, 0, 0, 0)
            shortcuts_layout.setSpacing(6)
            self._load_and_display_shortcuts(shortcuts_layout)
            shortcuts_layout.addStretch()

    def _open_eod_report(self):
        """Gün sonu raporunu aç."""
        report_dialog = EndOfDayReportDialog(
            self.db, self.dealer["code"], self
        )
        report_dialog.exec_()

    def closeEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        if self.camera:
            self.camera.stop()
        event.accept()
