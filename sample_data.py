#!/usr/bin/env python3
"""Deneme için örnek ürün ve bayi verisi ekler. Bir kez çalıştırın."""
from common.settings import load_settings
from common.database import Database, make_password_record

SAMPLE_PRODUCTS = [
    {"barcode": "8690000000011", "name": "Su 0.5L", "price": 10.0, "vat": 1,
     "stock": 500, "box_barcode": "18690000000011", "box_quantity": 24},
    {"barcode": "8690000000028", "name": "Çikolata 80g", "price": 45.0,
     "vat": 20, "stock": 200, "box_barcode": "18690000000028",
     "box_quantity": 12},
    {"barcode": "8690000000035", "name": "Süt 1L", "price": 32.5, "vat": 1,
     "stock": 150, "box_barcode": "18690000000035", "box_quantity": 10},
    {"barcode": "8690000000042", "name": "Ekmek", "price": 15.0, "vat": 1,
     "stock": 80, "box_barcode": "", "box_quantity": 1},
    {"barcode": "8690000000059", "name": "Deterjan 4kg", "price": 289.9,
     "vat": 20, "stock": 40, "box_barcode": "18690000000059",
     "box_quantity": 4},
]

SAMPLE_DEALERS = [
    {"code": "BAYI-001", "name": "Örnek Bayi", "address": "Merkez Mah. No:1",
     "phone": "0500 000 00 01", "username": "bayi1"},
    {"code": "BAYI-002", "name": "Şube 2", "address": "Sanayi Cad. No:12",
     "phone": "0500 000 00 02", "username": "bayi2"},
]
SAMPLE_PASSWORD = "123456"  # örnek kasa giriş şifresi (en az 6 karakter)


def main():
    settings = load_settings()
    db = Database(settings["mongo_uri"], settings["database_name"])
    db.verify_connection()

    for product in SAMPLE_PRODUCTS:
        if not db.products.find_one({"barcode": product["barcode"]}):
            db.add_product(dict(product))
            print(f"Ürün eklendi: {product['name']}")

    for dealer in SAMPLE_DEALERS:
        existing = db.dealers.find_one({"code": dealer["code"]})
        if not existing:
            record = dict(dealer)
            record.update(make_password_record(SAMPLE_PASSWORD))
            db.add_dealer(record)
            print(f"Bayi eklendi: {dealer['name']} "
                  f"(kullanıcı: {dealer['username']} / {SAMPLE_PASSWORD})")
        elif not existing.get("username"):
            update = {"username": dealer["username"]}
            update.update(make_password_record(SAMPLE_PASSWORD))
            db.update_dealer(dealer["code"], update)
            print(f"Bayi hesabı açıldı: {dealer['code']} "
                  f"(kullanıcı: {dealer['username']} / {SAMPLE_PASSWORD})")

    print("Örnek veriler hazır.")


if __name__ == "__main__":
    main()
