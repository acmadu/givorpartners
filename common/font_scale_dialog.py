"""Font boyutu ayarı dialog'u."""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton,
)
from PyQt5.QtCore import Qt
from common import style
from common.settings import save_settings


class FontScaleDialog(QDialog):
    """Font boyutunu ayarlamak için dialog."""

    def __init__(self, parent, settings: dict):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Yazı Boyutu Ayarla")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Yazı Boyutu", objectName="title")
        layout.addWidget(title)

        # Slider (0.8x - 1.5x = 80% - 150%)
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Küçük"))
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(80)  # 0.8x
        self.slider.setMaximum(150)  # 1.5x
        self.slider.setValue(int(style.FONT_SCALE * 100))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self.slider, 1)
        
        slider_layout.addWidget(QLabel("Büyük"))
        layout.addLayout(slider_layout)

        # Bilgi
        self.info_label = QLabel("", objectName="subtitle")
        self._update_info()
        layout.addWidget(self.info_label)

        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Sıfırla")
        reset_btn.clicked.connect(self._reset)
        button_layout.addWidget(reset_btn)
        
        ok_btn = QPushButton("Tamam", objectName="primary")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)

    def _on_slider_changed(self):
        """Slider değiştiğinde font scale'i güncelle."""
        scale = self.slider.value() / 100.0
        style.FONT_SCALE = scale
        self.settings["font_scale"] = scale
        self._update_info()
        # QSS'i hemen güncelle
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(style.build_qss())

    def _update_info(self):
        """Info label'ı güncelle."""
        scale_pct = int(style.FONT_SCALE * 100)
        self.info_label.setText(f"Geçerli Boyut: %{scale_pct}")

    def _reset(self):
        """Varsayılana dön."""
        self.slider.setValue(100)

    def accept(self):
        """Ayarları kaydet ve kapat."""
        save_settings(self.settings)
        super().accept()
