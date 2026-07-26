#!/usr/bin/env python3
"""
Mock Ingenico POS Terminal Sunucusu — Test amaçlı.

Çalıştırma:
  python3 ingenico_mock_server.py

Kasa config.json'da:
  "terminal_mode": "ingenico",
  "terminal_host": "127.0.0.1",
  "terminal_tcp_port": 8400

Ardından kasa "POS Terminal Ayarları" → Bağlantı Testi → başarılı olur.
Kredi Kartı ödeme yapınca sunucu onay gönderir.
"""

import socket
import struct
import sys

STX = 0x02
ETX = 0x03


def calculate_lrc(data: bytes) -> int:
    """LRC (Longitudinal Redundancy Check) hesapla."""
    lrc = 0
    for b in data:
        lrc ^= b
    return lrc


def handle_client(conn, addr):
    """Bir kasa bağlantısını işle."""
    print(f"[Bağlantı] {addr[0]}:{addr[1]} bağlandı")
    try:
        while True:
            # Kasa isteğini bekle
            raw = b""
            while True:
                chunk = conn.recv(1)
                if not chunk:
                    raise ConnectionResetError("Kasa bağlantısını kesti")
                raw += chunk
                if ETX in raw:
                    break

            # İsteği ayrıştır
            if raw[0] != STX:
                print(f"[Hata] Geçersiz STX: {raw[0]:02x}")
                continue

            # İçeriği çıkart (STX'den sonra, ETX'den önce)
            inner = raw[1:-2]  # ETX ve LRC'yi kaldır
            lrc_received = raw[-1]
            lrc_calc = calculate_lrc(inner + bytes([ETX]))

            if lrc_calc != lrc_received:
                print(f"[Hata] LRC hatalı: beklenen {lrc_calc:02x}, alınan {lrc_received:02x}")
                continue

            # Ingenico protokolü: "0200" + tutar(12) + "949"
            msg_type = inner[0:4].decode("ascii", errors="replace")
            amount_kurus = inner[4:16].decode("ascii", errors="replace")
            currency = inner[16:19].decode("ascii", errors="replace")

            amount_lira = float(amount_kurus) / 100
            print(f"[İstek] {msg_type} - {amount_lira:.2f} ₺ ({currency})")

            # Yanıt oluştur: "0210" + resp_code(2=onaylı) + auth_code(6) + ref_no(12) + card_last4(4)
            auth_code = "123456"
            ref_no = "000000123456"
            card_last4 = "4242"
            resp_code = "00"  # Onaylı

            response_body = (
                f"0210{resp_code}{auth_code}{ref_no}{card_last4}"
            ).encode("ascii")

            response_lrc = calculate_lrc(response_body + bytes([ETX]))
            response = bytes([STX]) + response_body + bytes([ETX, response_lrc])

            conn.sendall(response)
            print(f"[Yanıt] Onaylı — Auth: {auth_code}, Ref: {ref_no}")

    except ConnectionResetError as e:
        print(f"[Kapama] {e}")
    except Exception as e:
        print(f"[Hata] {e}")
    finally:
        conn.close()
        print(f"[Kapama] {addr[0]}:{addr[1]} bağlantısı kapandı")


def main():
    host = "127.0.0.1"
    port = 8400

    print(f"🖥  Mock Ingenico POS Sunucusu başlatılıyor...")
    print(f"📡 Dinleme: {host}:{port}")
    print(f"ℹ️  Kasa config.json'da şu ayarları kullan:")
    print(f'   "terminal_mode": "ingenico"')
    print(f'   "terminal_host": "{host}"')
    print(f'   "terminal_tcp_port": {port}')
    print()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)

    print(f"✅ Sunucu çalışıyor. Kasa'dan gelen bağlantıları bekliyorum...")
    print(f"(CTRL+C ile durdur)\n")

    try:
        while True:
            conn, addr = server.accept()
            # Her kasa bağlantısını ayrı işle
            handle_client(conn, addr)
    except KeyboardInterrupt:
        print("\n⏹  Sunucu durduruldu.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
