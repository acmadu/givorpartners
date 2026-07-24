"""Kamera ile karekod/barkod okuma (isteğe bağlı).

Gereksinimler: opencv-python, pyzbar ve sistemde zbar kütüphanesi.
Kurulu değilse CAMERA_SUPPORT False olur; kasa arayüzü bunu kontrol eder.
"""
import time

from PyQt5.QtCore import QThread, pyqtSignal

try:
    import cv2
    from pyzbar import pyzbar
    CAMERA_SUPPORT = True
except ImportError:
    CAMERA_SUPPORT = False


class CameraReader(QThread):
    """Kamerayı dinler, karekod/barkod bulduğunda sinyal yayar."""

    barcode_read = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        self._running = False

    def run(self):
        camera = cv2.VideoCapture(self.camera_index)
        if not camera.isOpened():
            self.error.emit("Kamera açılamadı.")
            return
        self._running = True
        last_read = ""
        last_time = 0.0
        while self._running:
            success, frame = camera.read()
            if not success:
                continue
            for code in pyzbar.decode(frame):
                data = code.data.decode("utf-8")
                now = time.monotonic()
                # Aynı kod 1,5 sn sonra tekrar okunabilir (çift ürün satışı)
                if data and (data != last_read or now - last_time > 1.5):
                    last_read = data
                    last_time = now
                    self.barcode_read.emit(data)
            self.msleep(80)
        camera.release()

    def stop(self):
        self._running = False
        self.wait(2000)
