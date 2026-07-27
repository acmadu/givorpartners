"""Fiziksel POS terminal entegrasyonu.

Desteklenen modlar
------------------
• manual   — Kasiyerin terminalde ödemeyi başlatıp sonucu elle onaylaması.
             Hiçbir ek kurulum gerektirmez; her terminal modeliyle çalışır.
• ingenico — Ingenico iCT220/250, Move 2500 vb. için TCP tabanlı EFT-POS
             protokolü (varsayılan port 8400). Ağ üzerinden bağlanır.
• serial   — Seri port (USB-Seri veya RS232) üzerinden terminal iletişimi.
             Gereksinim: `pip install pyserial`
• tcp      — Genel amaçlı TCP/IP (özel/başka marka terminaller).

Ingenico Protokolü (TCP)
------------------------
  İstek:   STX + "0200" + tutar(12 basamak, kuruş) + "949" + ETX + LRC
  Yanıt:   STX + "0210" + resp_code(2) + auth_code(6) + ref_no(12)
            + card_last4(4) + ETX + LRC
  resp_code "00" → onaylı, diğerleri → reddedildi.

Not: Gerçek banka/terminal protokolleri farklılık gösterebilir.
"""
from __future__ import annotations
import socket
import struct
from dataclasses import dataclass, field
from enum import Enum

# pyserial isteğe bağlı
try:
    import serial
    SERIAL_SUPPORT = True
except ImportError:
    SERIAL_SUPPORT = False

STX = 0x02
ETX = 0x03
ACK = 0x06
NAK = 0x15
TIMEOUT = 45  # saniye (müşteri kartını okutana kadar bekle)
CONNECT_TIMEOUT = 5  # bağlantı kurma zaman aşımı


class TerminalMode(str, Enum):
    MANUAL   = "manual"
    INGENICO = "ingenico"
    SERIAL   = "serial"
    TCP      = "tcp"
    SIMULATE = "simulate"


@dataclass
class PaymentResult:
    approved: bool
    amount: float
    auth_code: str  = ""       # Onay kodu (6 hane)
    ref_no: str     = ""       # Referans numarası
    card_last4: str = ""       # Kartın son 4 hanesi
    error_message: str = ""

    @property
    def summary(self) -> str:
        if self.approved:
            parts = [f"Onaylı — {self.amount:.2f} ₺"]
            if self.auth_code:
                parts.append(f"Onay: {self.auth_code}")
            if self.ref_no:
                parts.append(f"Ref: {self.ref_no}")
            return "  |  ".join(parts)
        return f"Reddedildi — {self.error_message or 'Terminal yanıt vermedi'}"


class PaymentTerminal:
    """Terminal bağlantısını yönetir ve ödeme isteği gönderir."""

    def __init__(self, settings: dict):
        self.mode     = TerminalMode(settings.get("terminal_mode", "manual"))
        self.port     = settings.get("terminal_port", "")
        self.baud     = int(settings.get("terminal_baud", 9600))
        self.host     = settings.get("terminal_host", "")
        self.tcp_port = int(settings.get("terminal_tcp_port",
                            6240 if settings.get("terminal_mode") == "ingenico"
                            else 8000))

    # --------------------------------------------------------- Public API
    def request_payment(self, amount: float) -> PaymentResult:
        """Terminale ödeme isteği gönderir; sonucu döndürür."""
        if self.mode == TerminalMode.MANUAL:
            return PaymentResult(approved=None, amount=amount)
        if self.mode == TerminalMode.SIMULATE:
            return self._simulate_payment(amount)
        if self.mode == TerminalMode.INGENICO:
            return self._ingenico_payment(amount)
        if self.mode == TerminalMode.SERIAL:
            return self._serial_payment(amount)
        if self.mode == TerminalMode.TCP:
            return self._tcp_payment(amount)
        return PaymentResult(approved=False, amount=amount,
                             error_message="Bilinmeyen terminal modu")

    def test_connection(self) -> tuple[bool, str]:
        """Terminal bağlantısını test eder. (ok, mesaj)"""
        if self.mode == TerminalMode.MANUAL:
            return True, "Manuel mod — bağlantı testi gerekmez."
        if self.mode == TerminalMode.SIMULATE:
            return True, "Simülasüon modu aktif — gerçek terminal gerekmez."
        if self.mode == TerminalMode.INGENICO:
            return self._test_ingenico()
        if self.mode == TerminalMode.SERIAL:
            return self._test_serial()
        if self.mode == TerminalMode.TCP:
            return self._test_tcp(self.host, self.tcp_port)
        return False, "Bilinmeyen mod"

    # --------------------------------------------------------- Protokol
    @staticmethod
    def _lrc(data: bytes) -> int:
        lrc = 0
        for b in data:
            lrc ^= b
        return lrc

    def _build_ingenico_request(self, amount_kurus: int) -> bytes:
        """Ingenico Move 3000F / ELPOS TCP istek paketi.

        Format (Türkiye ELPOS):
          [4 byte uzunluk (ASCII)] + [mesaj tipi 4 byte] + [tutar 12 byte] + [para birimi 3 byte]
          Veya eski format: STX + "0200" + amount(12) + "949" + ETX + LRC
        """
        # ELPOS format: length-prefixed
        payload = f"0200{amount_kurus:012d}949".encode("ascii")
        length = f"{len(payload):04d}".encode("ascii")
        return length + payload

    def _build_ingenico_request_legacy(self, amount_kurus: int) -> bytes:
        """Eski Ingenico STX/ETX/LRC formatı (iCT220/250 vb.)"""
        body = f"0200{amount_kurus:012d}949".encode("ascii")
        lrc = self._lrc(body + bytes([ETX]))
        return bytes([STX]) + body + bytes([ETX, lrc])

    def _parse_ingenico_response(self, data: bytes,
                                  amount: float) -> PaymentResult:
        """Ingenico EFT-POS yanıtını ayrıştırır. ELPOS ve STX/ETX formatlarını destekler."""
        if not data:
            return PaymentResult(approved=False, amount=amount,
                                 error_message="Terminal yanıt vermedi")
        try:
            # ELPOS: ilk 4 byte uzunluk (ASCII rakam)
            if data[:4].isdigit():
                inner = data[4:].decode("ascii", errors="replace")
            elif data[0] == STX:
                # Legacy STX/ETX
                inner = data[1:-2].decode("ascii", errors="replace")
            else:
                inner = data.decode("ascii", errors="replace")

            msg_type  = inner[0:4]
            resp_code = inner[4:6]
            auth_code = inner[6:12].strip()
            ref_no    = inner[12:24].strip()
            card_last4 = inner[24:28].strip() if len(inner) >= 28 else ""
        except Exception as exc:
            return PaymentResult(approved=False, amount=amount,
                                 error_message=f"Yanıt ayrıştırılamadı: {exc}")

        if resp_code == "00":
            return PaymentResult(approved=True, amount=amount,
                                 auth_code=auth_code, ref_no=ref_no,
                                 card_last4=card_last4)
        return PaymentResult(
            approved=False, amount=amount,
            error_message=_ingenico_error(resp_code),
        )

    @staticmethod
    def _build_message(amount_kurus: int, currency: str = "TRY") -> bytes:
        """Genel seri/TCP protokol paketi (serial / tcp modları için)."""
        payload = f"{amount_kurus:012d}{currency}".encode()
        length  = f"{len(payload):04d}".encode()
        body    = length + payload
        lrc = 0
        for b in body:
            lrc ^= b
        return bytes([STX]) + body + bytes([ETX, lrc])

    @staticmethod
    def _parse_response(data: bytes) -> PaymentResult | None:
        """Genel protokol yanıtını ayrıştırır (serial / tcp modları)."""
        if len(data) < 4 or data[0] != STX:
            return None
        payload = data[1:-2]
        try:
            resp_code = payload[4:6].decode("ascii", errors="replace")
            auth_code = payload[6:12].decode("ascii", errors="replace").strip()
            ref_no    = payload[12:24].decode("ascii", errors="replace").strip()
        except Exception:
            return None
        approved = resp_code == "00"
        return PaymentResult(
            approved=approved, amount=0,
            auth_code=auth_code if approved else "",
            ref_no=ref_no if approved else "",
            error_message="" if approved else f"Hata kodu: {resp_code}",
        )

    # --------------------------------------------------------- Simülasüon
    def _simulate_payment(self, amount: float) -> PaymentResult:
        """
        Simülasüon modu: PyQt5 dialog ile kullanıcıya onay/ret sor.
        Bu metot arka plan thread'inden çağrılır, PyQt5 sinyali ile
        ana thread'e görev göndermek yerine blocking QMessageBox yerine
        bir sentinel PaymentResult döndürür.
        Gerçek dialog CardPaymentDialog tarafından simülasüon modünde
        farklı render edilir.
        """
        import random, time
        time.sleep(1.5)   # gerçek terminal gecikmesi simüle et
        # Sahte onay verisi üret
        auth = f"{random.randint(100000, 999999)}"
        ref  = f"{random.randint(10**11, 10**12 - 1)}"
        last4 = f"{random.randint(1000, 9999)}"
        return PaymentResult(
            approved=True, amount=amount,
            auth_code=auth, ref_no=ref, card_last4=last4,
            error_message=""
        )

    # --------------------------------------------------------- Ingenico TCP
    def _ingenico_payment(self, amount: float) -> PaymentResult:
        if not self.host:
            return PaymentResult(approved=False, amount=amount,
                                 error_message="Terminal IP adresi ayarlanmamış "
                                               "(Ayarlar → POS Terminali)")
        port = self.tcp_port if self.tcp_port else 6240
        kurus = round(amount * 100)
        last_error = ""

        # Önce ELPOS (length-prefixed) dene, başarısızsa legacy STX/ETX dene
        for request_fn in (self._build_ingenico_request,
                           self._build_ingenico_request_legacy):
            try:
                raw = self._ingenico_exchange(port, request_fn(kurus))
            except socket.timeout:
                last_error = ("Terminal zaman aşımı — müşteri ödeme yapmadı "
                              "veya terminal yanıt vermedi.")
                continue
            except ConnectionRefusedError:
                return PaymentResult(
                    approved=False, amount=amount,
                    error_message=(f"Bağlantı reddedildi — {self.host}:{port}\n"
                                   "Terminal açık mı? IP/port doğru mu?"))
            except OSError as exc:
                return PaymentResult(
                    approved=False, amount=amount,
                    error_message=(f"Terminale ulaşılamadı: {exc}\n"
                                   f"IP: {self.host}  Port: {port}"))
            except Exception as exc:
                last_error = str(exc)
                continue

            if not raw:
                last_error = "Terminal yanıt vermedi"
                continue
            return self._parse_ingenico_response(raw, amount)

        return PaymentResult(approved=False, amount=amount,
                             error_message=last_error or "Terminal yanıt vermedi")

    def _ingenico_exchange(self, port: int, request: bytes) -> bytes:
        """Terminale istek gönderip yanıtı okur."""
        with socket.create_connection(
                (self.host, port), timeout=CONNECT_TIMEOUT) as sock:
            sock.settimeout(TIMEOUT)
            sock.sendall(request)
            raw = b""
            while True:
                chunk = sock.recv(256)
                if not chunk:
                    break
                raw += chunk
                if ETX in raw:
                    break
                if len(raw) >= 4 and raw[:4].isdigit():
                    if len(raw) >= 4 + int(raw[:4]):
                        break
            return raw

    # --------------------------------------------------------- Serial
    def _serial_payment(self, amount: float) -> PaymentResult:
        if not SERIAL_SUPPORT:
            return PaymentResult(approved=False, amount=amount,
                                 error_message="pyserial kurulu değil: pip install pyserial")
        if not self.port:
            return PaymentResult(approved=False, amount=amount,
                                 error_message="Seri port ayarlanmamış (config.json: terminal_port)")
        try:
            with serial.Serial(self.port, self.baud, timeout=TIMEOUT) as ser:
                kurus = round(amount * 100)
                ser.write(self._build_message(kurus))
                raw = ser.read(64)
            result = self._parse_response(raw)
            if result is None:
                return PaymentResult(approved=False, amount=amount,
                                     error_message="Geçersiz terminal yanıtı")
            result.amount = amount
            return result
        except Exception as error:
            return PaymentResult(approved=False, amount=amount,
                                 error_message=str(error))

    def _test_serial(self) -> tuple[bool, str]:
        if not SERIAL_SUPPORT:
            return False, "pyserial kurulu değil: pip install pyserial"
        if not self.port:
            return False, "terminal_port ayarlanmamış"
        try:
            with serial.Serial(self.port, self.baud, timeout=2):
                pass
            return True, f"Seri port {self.port} açıldı."
        except Exception as error:
            return False, str(error)

    # --------------------------------------------------------- TCP (genel)
    def _tcp_payment(self, amount: float) -> PaymentResult:
        if not self.host:
            return PaymentResult(approved=False, amount=amount,
                                 error_message="Terminal IP adresi ayarlanmamış (terminal_host)")
        try:
            with socket.create_connection(
                    (self.host, self.tcp_port), timeout=TIMEOUT) as sock:
                kurus = round(amount * 100)
                sock.sendall(self._build_message(kurus))
                raw = sock.recv(64)
            result = self._parse_response(raw)
            if result is None:
                return PaymentResult(approved=False, amount=amount,
                                     error_message="Geçersiz terminal yanıtı")
            result.amount = amount
            return result
        except Exception as error:
            return PaymentResult(approved=False, amount=amount,
                                 error_message=str(error))

    def _test_tcp(self, host: str, port: int) -> tuple[bool, str]:
        if not host:
            return False, "Terminal IP adresi ayarlanmamış (Ayarlar → POS Terminali)"
        try:
            with socket.create_connection((host, port), timeout=CONNECT_TIMEOUT):
                pass
            return True, f"Bağlantı başarılı: {host}:{port}"
        except ConnectionRefusedError:
            return False, (f"Bağlantı reddedildi: {host}:{port}\n"
                           "Terminal açık mı? Doğru port mu?")
        except socket.timeout:
            return False, (f"Zaman aşımı: {host}:{port}\n"
                           "IP doğru mu? Terminal aynı ağda mı?")
        except OSError as e:
            return False, f"Terminale ulaşılamadı: {e}\nIP: {host}  Port: {port}"

    def _test_ingenico(self) -> tuple[bool, str]:
        """Ingenico terminalini bilinen portlarda dener."""
        if not self.host:
            return False, "Terminal IP adresi ayarlanmamış (Ayarlar → POS Terminali)"
        ports = [self.tcp_port] if self.tcp_port else []
        for candidate in (6240, 8400, 4444, 9999):
            if candidate not in ports:
                ports.append(candidate)
        errors = []
        for port in ports:
            ok, msg = self._test_tcp(self.host, port)
            if ok:
                if port != self.tcp_port:
                    return True, (f"{msg}\n\nAyarlardaki portu {port} olarak "
                                  "güncelleyin.")
                return True, msg
            errors.append(f"{port}: {msg.splitlines()[0]}")
        return False, ("Terminale bağlanılamadı.\n\n"
                       "• Terminal açık ve ağa bağlı mı?\n"
                       "• IP adresi doğru mu?\n"
                       "• Kasa ile terminal aynı ağda mı?\n\n"
                       "Denenen portlar:\n" + "\n".join(errors))


def _ingenico_error(code: str) -> str:
    """Ingenico hata kodunu Türkçe açıklamaya çevirir."""
    _MAP = {
        "01": "Bankayı arayın",
        "04": "Kart iptal edildi",
        "05": "İşlem onaylanmadı",
        "12": "Geçersiz işlem",
        "13": "Geçersiz tutar",
        "14": "Kart numarası hatalı",
        "30": "Format hatası",
        "41": "Kayıp kart",
        "43": "Çalıntı kart",
        "51": "Yetersiz bakiye",
        "54": "Kartın süresi dolmuş",
        "55": "PIN hatalı",
        "57": "Kart bu işlem tipine izin vermiyor",
        "61": "Para çekme limiti aşıldı",
        "62": "Kısıtlı kart",
        "65": "Para çekme sınırı aşıldı",
        "75": "PIN denemesi aşıldı",
        "76": "Geçersiz hesap",
        "91": "Banka sistemine ulaşılamıyor",
        "96": "Sistem arızası",
    }
    return _MAP.get(code, f"Terminal hata kodu: {code}")
