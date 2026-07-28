"""Gün sonu detaylı satış raporu."""
import logging
from datetime import datetime, date
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
    QMessageBox, QTabWidget, QTextEdit
)
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtCore import QDate
from pymongo.errors import PyMongoError
from common import style

logger = logging.getLogger(__name__)

# strftime('%A') i\u015fletim sistemi diline ba\u011fl\u0131d\u0131r; rapor her makinede
# T\u00fcrk\u00e7e g\u00f6r\u00fcns\u00fcn diye g\u00fcn adlar\u0131 sabit tutulur.
WEEKDAYS_TR = ("Pazartesi", "Salı", "Çarşamba", "Perşembe",
               "Cuma", "Cumartesi", "Pazar")


class EndOfDayReportDialog(QDialog):
    """Gün sonu detaylı raporu."""

    def __init__(self, db, dealer_code: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.dealer_code = dealer_code
        self.setWindowTitle("📊 Gün Sonu Raporu")
        self.resize(1200, 700)
        
        # Favicon
        icon_path = "assets/favicon.ico"
        if __import__('os').path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self._build_ui()
        self._load_today_report()

    def _build_ui(self):
        """Arayüz oluştur."""
        layout = QVBoxLayout()

        # Tarih seçimi
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tarih:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.dateChanged.connect(self._load_report)
        filter_layout.addWidget(self.date_input)
        filter_layout.addStretch()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._load_report)
        filter_layout.addWidget(refresh_btn)
        layout.addLayout(filter_layout)

        # Tab widget
        tabs = QTabWidget()

        # ---- Tab 1: Özet ----
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Courier", 10))
        summary_layout.addWidget(self.summary_text)
        tabs.addTab(summary_widget, "📈 Özet")

        # ---- Tab 2: Satışlar ----
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels(
            ["Zaman", "Müşteri", "Ürün", "Adet", "Birim Fiyat", "Toplam", "Ödeme Türü"]
        )
        self.sales_table.horizontalHeader().setStretchLastSection(True)
        self.sales_table.setAlternatingRowColors(True)
        sales_layout.addWidget(self.sales_table)
        tabs.addTab(sales_widget, "🛒 Satış Detayları")

        # ---- Tab 3: Ödeme Türleri ----
        payment_widget = QWidget()
        payment_layout = QVBoxLayout(payment_widget)

        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(3)
        self.payment_table.setHorizontalHeaderLabels(
            ["Ödeme Türü", "Miktar", "Toplam"]
        )
        self.payment_table.horizontalHeader().setStretchLastSection(True)
        self.payment_table.setAlternatingRowColors(True)
        payment_layout.addWidget(self.payment_table)
        tabs.addTab(payment_widget, "💳 Ödeme Yöntemleri")

        # ---- Tab 4: Ürün Detayları ----
        product_widget = QWidget()
        product_layout = QVBoxLayout(product_widget)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(
            ["Barkod", "Ürün Adı", "Adet", "Toplam Satış", "Ortalama Fiyat"]
        )
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.setAlternatingRowColors(True)
        product_layout.addWidget(self.product_table)
        tabs.addTab(product_widget, "📦 Ürün Satışları")

        layout.addWidget(tabs)

        # Alt butonlar
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📄 Excel'e Dışa Aktar")
        export_btn.clicked.connect(self._export_to_excel)
        button_layout.addWidget(export_btn)

        print_btn = QPushButton("🖨 Yazdır")
        print_btn.clicked.connect(self._print_report)
        button_layout.addWidget(print_btn)

        button_layout.addStretch()

        close_btn = QPushButton("✖ Kapat")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_report(self):
        """Raporu yükle."""
        # PyQt5'te QDate.toPyDate() kullanılır (toPython() PySide'a özgüdür).
        selected_date = self.date_input.date().toPyDate()
        self._load_today_report(selected_date)

    def _load_today_report(self, report_date: date = None):
        """Belirtilen günün satış raporunu yükle."""
        if report_date is None:
            report_date = date.today()

        try:
            # Günün başı ve sonu
            start_time = datetime(report_date.year, report_date.month, report_date.day, 0, 0, 0)
            end_time = datetime(report_date.year, report_date.month, report_date.day, 23, 59, 59)

            # Satışları getir — kayıtlarda tarih alanı "date" olarak tutulur.
            sales = list(self.db.sales.find({
                "dealer_code": self.dealer_code,
                "date": {"$gte": start_time, "$lte": end_time}
            }).sort("date", 1))

            # Özet hesapla
            total_sales = sum(s.get("total", 0) for s in sales)
            total_items = sum(
                item.get("quantity", 0)
                for s in sales for item in s.get("items", [])
            )
            num_transactions = len(sales)

            # Ödeme türleri (tutar ve işlem adedi)
            payment_summary = {}
            payment_counts = {}
            for sale in sales:
                payment_type = sale.get("payment_type", "NAKİT")
                payment_summary[payment_type] = payment_summary.get(payment_type, 0) + sale.get("total", 0)
                payment_counts[payment_type] = payment_counts.get(payment_type, 0) + 1

            # Ürün detayları
            product_summary = {}
            for sale in sales:
                for item in sale.get("items", []):
                    barcode = item.get("barcode", "?")
                    name = item.get("name", "?")
                    qty = item.get("quantity", 0)
                    price = item.get("unit_price", 0)
                    
                    if barcode not in product_summary:
                        product_summary[barcode] = {
                            "name": name,
                            "quantity": 0,
                            "total": 0,
                            "count": 0
                        }
                    
                    product_summary[barcode]["quantity"] += qty
                    product_summary[barcode]["total"] += qty * price
                    product_summary[barcode]["count"] += 1

            # Özet metni oluştur
            summary_text = f"""
╔════════════════════════════════════════════════════════════════╗
║                        GÜN SONU RAPORU                          ║
╠════════════════════════════════════════════════════════════════╣
║ Tarih: {report_date.strftime('%d.%m.%Y')} ({WEEKDAYS_TR[report_date.weekday()]})
║ Bayi: {self.dealer_code}
╠════════════════════════════════════════════════════════════════╣
║ GENEL TOPLAM
║   Toplam Satış: {total_sales:,.2f} ₺
║   İşlem Sayısı: {num_transactions}
║   Toplam Ürün: {total_items} adet
╠════════════════════════════════════════════════════════════════╣
║ ÖDEME YÖNTEMLERI
"""
            for payment_type, amount in sorted(payment_summary.items(), key=lambda x: x[1], reverse=True):
                pct = (amount / total_sales * 100) if total_sales > 0 else 0
                summary_text += f"║   {payment_type:15s}: {amount:>12,.2f} ₺  ({pct:5.1f}%)\n"

            summary_text += f"""║
╠════════════════════════════════════════════════════════════════╣
║ EN ÇOK SATILAN ÜRÜNLER (Top 10)
"""
            top_products = sorted(
                product_summary.items(),
                key=lambda x: x[1]["quantity"],
                reverse=True
            )[:10]

            for i, (barcode, data) in enumerate(top_products, 1):
                summary_text += f"║ {i:2d}. {data['name'][:30]:30s}  {data['quantity']:>4.0f} adet  {data['total']:>10,.2f} ₺\n"

            summary_text += "╚════════════════════════════════════════════════════════════════╝\n"

            self.summary_text.setText(summary_text)

            # Satış tablosunu doldur
            self._populate_sales_table(sales)

            # Ödeme tablosunu doldur
            self._populate_payment_table(payment_summary, payment_counts)

            # Ürün tablosunu doldur
            self._populate_product_table(product_summary)

        except PyMongoError as e:
            QMessageBox.critical(self, "Hata", f"Veritabanı hatası: {str(e)}")
            logger.error(f"DB error loading report: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor oluşturulamadı: {e}")
            logger.exception("Gün sonu raporu oluşturulamadı")

    def _populate_sales_table(self, sales: list):
        """Satış tablosunu doldur."""
        self.sales_table.setRowCount(0)
        
        all_items = []
        for sale in sales:
            sale_time = sale.get("date", datetime.now())
            payment_method = sale.get("payment_type", "NAKİT")
            
            for item in sale.get("items", []):
                all_items.append((
                    sale_time,
                    sale.get("customer_name", "Bilinmiyor"),
                    item.get("name", "?"),
                    item.get("quantity", 0),
                    item.get("unit_price", 0),
                    item.get("quantity", 0) * item.get("unit_price", 0),
                    payment_method
                ))

        self.sales_table.setRowCount(len(all_items))
        for row, (time, customer, product, qty, price, total, payment) in enumerate(all_items):
            self.sales_table.setItem(row, 0, QTableWidgetItem(time.strftime("%H:%M:%S")))
            self.sales_table.setItem(row, 1, QTableWidgetItem(customer))
            self.sales_table.setItem(row, 2, QTableWidgetItem(product))
            self.sales_table.setItem(row, 3, QTableWidgetItem(f"{qty:.0f}"))
            self.sales_table.setItem(row, 4, QTableWidgetItem(f"{price:,.2f} ₺"))
            self.sales_table.setItem(row, 5, QTableWidgetItem(f"{total:,.2f} ₺"))
            self.sales_table.setItem(row, 6, QTableWidgetItem(payment))

    def _populate_payment_table(self, payment_summary: dict, payment_counts: dict):
        """Ödeme tablosunu doldur."""
        self.payment_table.setRowCount(len(payment_summary))
        
        for row, (payment_type, amount) in enumerate(sorted(payment_summary.items(), 
                                                            key=lambda x: x[1], 
                                                            reverse=True)):
            # Adet, seçilen güne ait işlem sayısıdır (tüm geçmiş değil).
            count = payment_counts.get(payment_type, 0)
            
            self.payment_table.setItem(row, 0, QTableWidgetItem(payment_type))
            self.payment_table.setItem(row, 1, QTableWidgetItem(f"{count}"))
            self.payment_table.setItem(row, 2, QTableWidgetItem(f"{amount:,.2f} ₺"))

    def _populate_product_table(self, product_summary: dict):
        """Ürün tablosunu doldur."""
        self.product_table.setRowCount(len(product_summary))
        
        for row, (barcode, data) in enumerate(sorted(product_summary.items(),
                                                     key=lambda x: x[1]["quantity"],
                                                     reverse=True)):
            avg_price = data["total"] / data["quantity"] if data["quantity"] > 0 else 0
            
            self.product_table.setItem(row, 0, QTableWidgetItem(barcode))
            self.product_table.setItem(row, 1, QTableWidgetItem(data["name"]))
            self.product_table.setItem(row, 2, QTableWidgetItem(f"{data['quantity']:.0f}"))
            self.product_table.setItem(row, 3, QTableWidgetItem(f"{data['total']:,.2f} ₺"))
            self.product_table.setItem(row, 4, QTableWidgetItem(f"{avg_price:,.2f} ₺"))

    def _export_to_excel(self):
        """Excel'e dışa aktar."""
        QMessageBox.information(self, "Bilgi", "Excel dışa aktarma özelliği yakında eklenecek!")

    def _print_report(self):
        """Raporu yazdır."""
        QMessageBox.information(self, "Bilgi", "Yazdırma özelliği yakında eklenecek!")
