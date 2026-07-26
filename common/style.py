"""Ayarlanabilir tema sistemi.

THEMES sözlüğündeki her palet aynı anahtarları içerir; build_qss()
seçilen paletten QSS üretir. Çalışma zamanında renk gereken yerler
(ör. stok grafiği) palette() üzerinden güncel paleti okur.

Animasyonlar: animate_button() ve fade_in_widget() yardımcı fonksiyonları
sayfalar arası geçişlerde ve buton tıklamalarında kullanılır.
"""
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect

THEMES = {
    "night_mint": {
        "display": "🌿 Gece Nanesi",
        "bg": "#12101d", "panel": "#1a1729", "card": "#221e35",
        "border": "#332d4f", "accent": "#00d4aa", "accent_dark": "#00a583",
        "secondary": "#8b7bff", "green": "#38e07b", "red": "#ff5d6c",
        "yellow": "#ffb454", "text": "#f2f0fa", "muted": "#9a93b8",
        "on_accent": "#0c0a16", "hover": "#2c2745", "pressed": "#191530",
        "alt_row": "#1f1b31", "scroll": "#3d3560",
        "sidebar1": "#1c1830", "sidebar2": "#151226",
    },
    "ocean": {
        "display": "🌊 Okyanus",
        "bg": "#0c1220", "panel": "#111a2e", "card": "#16233c",
        "border": "#24365a", "accent": "#38bdf8", "accent_dark": "#0e93cf",
        "secondary": "#818cf8", "green": "#34d399", "red": "#fb7185",
        "yellow": "#fbbf24", "text": "#eef4ff", "muted": "#8497b8",
        "on_accent": "#06121f", "hover": "#1d2d4d", "pressed": "#101a30",
        "alt_row": "#131e35", "scroll": "#2d4166",
        "sidebar1": "#101a30", "sidebar2": "#0a101d",
    },
    "amber": {
        "display": "🔥 Kehribar",
        "bg": "#171210", "panel": "#211a16", "card": "#2b211c",
        "border": "#453427", "accent": "#fbbf24", "accent_dark": "#d19a10",
        "secondary": "#fb923c", "green": "#4ade80", "red": "#f87171",
        "yellow": "#facc15", "text": "#faf4ec", "muted": "#b3a08c",
        "on_accent": "#211505", "hover": "#382b22", "pressed": "#1c1512",
        "alt_row": "#251d18", "scroll": "#54402e",
        "sidebar1": "#241c17", "sidebar2": "#191310",
    },
    "light": {
        "display": "☀️ Aydınlık",
        "bg": "#ffffff", "panel": "#f8f9fa", "card": "#ffffff",
        "border": "#dee2e6", "accent": "#0d9488", "accent_dark": "#0b7a70",
        "secondary": "#6366f1", "green": "#16a34a", "red": "#dc2626",
        "yellow": "#d97706", "text": "#1f2937", "muted": "#6b7280",
        "on_accent": "#ffffff", "hover": "#f0f4f8", "pressed": "#e5e7eb",
        "alt_row": "#f9fafb", "scroll": "#bfdbfe",
        "sidebar1": "#f3f4f6", "sidebar2": "#e5e7eb",
    },
}

DEFAULT_THEME = "night_mint"
FONT_SCALE = 1.0  # 1.0 = normal, 1.2 = +20% büyük, vb.

_current_name = DEFAULT_THEME


def set_theme(name: str):
    global _current_name
    _current_name = name if name in THEMES else DEFAULT_THEME


def current_theme_name() -> str:
    return _current_name


def palette() -> dict:
    """Seçili temanın renk paletini döndürür."""
    return THEMES[_current_name]


def _rgba(hex_color: str, alpha: float) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def build_qss(name: str = None) -> str:
    """Verilen (ya da seçili) tema için QSS üretir."""
    if name:
        set_theme(name)
    p = palette()
    base_font = int(14 * FONT_SCALE)
    header_font = int(13 * FONT_SCALE)
    title_font = int(22 * FONT_SCALE)
    large_font = int(42 * FONT_SCALE)
    small_font = int(11 * FONT_SCALE)
    card_value = int(28 * FONT_SCALE)
    barcode_font = int(20 * FONT_SCALE)
    return f"""
* {{
    font-family: "Adwaita Sans", "Inter", "Cantarell", "Noto Sans",
                 "Segoe UI", sans-serif;
    font-size: {base_font}px;
    font-weight: 400;
    color: {p["text"]};
}}
QMainWindow, QDialog {{
    background-color: {p["bg"]};
}}
QWidget#sidebar {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {p["sidebar1"]}, stop:1 {p["sidebar2"]});
    border-right: 2px solid {p["border"]};
}}
QWidget#card {{
    background-color: {p["card"]};
    border: 1px solid {p["border"]};
    border-radius: 16px;
}}
QLabel#title {{
    font-size: {title_font}px;
    font-weight: 600;
}}
QLabel#logoText {{
    font-size: {int(19 * FONT_SCALE)}px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: {p["accent"]};
}}
QLabel#subtitle {{
    font-size: {header_font}px;
    color: {p["muted"]};
}}
QLabel#cardValue {{
    font-size: {card_value}px;
    font-weight: 600;
    color: {p["accent"]};
}}
QLabel#cardTitle {{
    font-size: {small_font}px;
    font-weight: 500;
    color: {p["muted"]};
    letter-spacing: 1px;
}}
QLabel#totalAmount {{
    font-size: {large_font}px;
    font-weight: 600;
    color: {p["green"]};
}}
QPushButton {{
    background-color: {p["card"]};
    border: 1px solid {p["border"]};
    border-radius: 10px;
    padding: {int(12 * FONT_SCALE)}px {int(20 * FONT_SCALE)}px;
    font-size: {base_font}px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {p["hover"]};
    border-color: {p["accent"]};
    color: {p["accent"]};
}}
QPushButton:pressed {{
    background-color: {p["pressed"]};
    border-color: {p["accent"]};
}}
QPushButton#primary {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p["accent"]}, stop:0.5 {p["secondary"]}, stop:1 {p["accent"]});
    border: none;
    color: {p["on_accent"]};
    font-weight: 600;
    min-height: 64px;
}}
QPushButton#primary:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p["accent_dark"]}, stop:0.5 {p["secondary"]});
}}
QPushButton#primary:pressed {{
    background-color: {p["accent_dark"]};
}}
QPushButton#success {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["green"]}, stop:1 {_rgba(p["green"], 0.8)});
    border: none;
    color: white;
    font-weight: 600;
    min-height: 64px;
}}
QPushButton#success:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["green"]}, stop:1 {p["green"]});
}}
QPushButton#secondary {{
    background-color: {p["panel"]};
    border: 1px solid {p["border"]};
    color: {p["text"]};
    font-weight: 500;
}}
QPushButton#secondary:hover {{
    background-color: {p["hover"]};
    border-color: {p["secondary"]};
    color: {p["secondary"]};
}}
QPushButton#secondary:pressed {{
    background-color: {p["pressed"]};
    border-color: {p["secondary"]};
}}
QPushButton#danger {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["red"]}, stop:1 {_rgba(p["red"], 0.8)});
    border: none;
    color: white;
    font-weight: 600;
    min-height: 56px;
}}
QPushButton#danger:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["red"]}, stop:1 {p["red"]});
}}
QPushButton#navButton {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 13px 18px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
    color: {p["muted"]};
}}
QPushButton#navButton:hover {{
    color: {p["text"]};
    background-color: {_rgba(p["secondary"], 0.08)};
    border-left-color: {p["secondary"]};
}}
QPushButton#navButton:checked {{
    color: {p["accent"]};
    background-color: {_rgba(p["accent"], 0.10)};
    border-left-color: {p["accent"]};
}}
QPushButton#fullscreenButton {{
    background: transparent;
    border: 1px solid {p["border"]};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 14px;
    color: {p["muted"]};
}}
QPushButton#fullscreenButton:hover {{
    color: {p["accent"]};
    border-color: {p["accent"]};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background-color: {p["panel"]};
    border: 1px solid {p["border"]};
    border-radius: 10px;
    padding: {int(11 * FONT_SCALE)}px {int(14 * FONT_SCALE)}px;
    font-size: {base_font}px;
    selection-background-color: {p["accent"]};
    selection-color: {p["on_accent"]};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 2px solid {p["accent"]};
    padding: {int(8 * FONT_SCALE)}px {int(11 * FONT_SCALE)}px;
}}
QLineEdit#barcodeInput {{
    font-size: {barcode_font}px;
    font-weight: 500;
    padding: {int(16 * FONT_SCALE)}px {int(18 * FONT_SCALE)}px;
    border: 2px solid {p["accent"]};
    border-radius: 14px;
    background-color: {p["card"]};
    font-family: "Adwaita Mono", "Liberation Mono", "Consolas", monospace;
    letter-spacing: 1px;
}}
QTableWidget {{
    background-color: {p["panel"]};
    alternate-background-color: {p["alt_row"]};
    border: 1px solid {p["border"]};
    border-radius: 12px;
    gridline-color: transparent;
    font-size: {base_font}px;
}}
QTableWidget::item {{
    padding: {int(10 * FONT_SCALE)}px;
    border-bottom: 1px solid {p["border"]};
}}
QTableWidget::item:selected {{
    background-color: {_rgba(p["accent"], 0.22)};
    color: {p["text"]};
}}
QHeaderView::section {{
    background-color: transparent;
    border: none;
    border-bottom: 2px solid {p["accent_dark"]};
    padding: {int(12 * FONT_SCALE)}px {int(10 * FONT_SCALE)}px;
    font-weight: 600;
    font-size: {header_font}px;
    letter-spacing: 0.5px;
    color: {p["muted"]};
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {p["scroll"]};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p["secondary"]};
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background: {p["scroll"]};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
    width: 0;
}}
QMessageBox {{
    background-color: {p["panel"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background-color: {p["card"]};
    border: 1px solid {p["border"]};
    selection-background-color: {p["accent"]};
    selection-color: {p["on_accent"]};
    font-size: {base_font}px;
    padding: {int(5 * FONT_SCALE)}px 0;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
"""


def animate_button_press(button, duration_ms: int = 100):
    """Butona tıklama animasyonu (scale + opacity).
    
    Çağrı: button.pressed.connect(lambda: animate_button_press(button))
    """
    anim = QPropertyAnimation(button, b"geometry")
    anim.setDuration(duration_ms)
    anim.setStartValue(button.geometry())
    rect = button.geometry()
    rect.adjust(2, 2, -2, -2)  # 4px küçüle
    anim.setEndValue(rect)
    anim.setEasingCurve(QEasingCurve.OutQuad)
    anim.start(QPropertyAnimation.KeepWhenStopped)
    # Geri dön
    anim2 = QPropertyAnimation(button, b"geometry")
    anim2.setDuration(duration_ms // 2)
    anim2.setStartValue(rect)
    anim2.setEndValue(button.geometry())
    anim2.setEasingCurve(QEasingCurve.OutQuad)
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(duration_ms, lambda: anim2.start(QPropertyAnimation.KeepWhenStopped))


def fade_in_widget(widget: QWidget, duration_ms: int = 400):
    """Widget'a fade-in animasyonu (0 → 1 opacity).
    
    Çağrı: fade_in_widget(page)
    """
    effect = QGraphicsOpacityEffect()
    effect.setOpacity(0)
    widget.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.InOutQuad)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    
    def remove_effect():
        widget.setGraphicsEffect(None)
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(duration_ms, remove_effect)
