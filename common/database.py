"""MongoDB database layer.

Collections:
- products: {barcode, box_barcode, box_quantity, name, price, vat, stock, active}
- dealers : {code, name, address, phone, username, password_hash, salt, active}
- sales   : {dealer_code, date, items[], total, payment_type}

Eski Türkçe şemadaki veriler ilk bağlantıda otomatik olarak
İngilizce şemaya taşınır (bkz. _migrate_legacy_data).
"""
import hashlib
import re
import secrets
from datetime import datetime, timedelta

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

# Eski koleksiyon adları -> yeni adlar
LEGACY_COLLECTIONS = {
    "urunler": "products",
    "bayiler": "dealers",
    "satislar": "sales",
}

# Eski alan adları -> yeni alan adları (koleksiyon bazında)
LEGACY_FIELDS = {
    "products": {
        "barkod": "barcode", "koli_barkod": "box_barcode",
        "koli_adet": "box_quantity", "ad": "name", "fiyat": "price",
        "kdv": "vat", "stok": "stock", "aktif": "active",
    },
    "dealers": {
        "kod": "code", "ad": "name", "adres": "address",
        "telefon": "phone", "aktif": "active",
    },
    "sales": {
        "bayi_kodu": "dealer_code", "tarih": "date", "kalemler": "items",
        "toplam": "total", "odeme_turu": "payment_type",
    },
}

LEGACY_ITEM_FIELDS = {
    "barkod": "barcode", "ad": "name", "adet": "quantity",
    "birim_fiyat": "unit_price",
}


class DatabaseError(Exception):
    """Veritabanına ulaşılamadığında fırlatılır."""


def _hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"),
        bytes.fromhex(salt_hex), 100_000).hex()


def make_password_record(password: str) -> dict:
    """Yeni tuz üretip parolayı PBKDF2 ile özetler."""
    salt = secrets.token_hex(16)
    return {"salt": salt, "password_hash": _hash_password(password, salt)}


class Database:
    def __init__(self, uri: str, database_name: str = "yazarkasa"):
        # mongodb+srv:// DNS SRV resolution sorunları yaşanıyorsa, direkt mongodb:// kullan
        if "mongodb+srv://" in uri:
            uri = uri.replace("mongodb+srv://", "mongodb://", 1)
            # .mongodb.net kaldırıp .mongodb.net:27017 yap (direct connection)
            if ".mongodb.net" in uri and ":27017" not in uri:
                # mongodb://user:pass@host.mongodb.net/?... → mongodb://user:pass@host.mongodb.net:27017/?...
                uri = uri.replace(".mongodb.net/?", ".mongodb.net:27017/?")
                uri = uri.replace(".mongodb.net?", ".mongodb.net:27017?")
        
        self._client = MongoClient(uri, serverSelectionTimeoutMS=30000, socketTimeoutMS=30000)
        self.db = self._client[database_name]
        self.products = self.db["products"]
        self.dealers = self.db["dealers"]
        self.sales = self.db["sales"]
        self.dealer_stocks = self.db["dealer_stocks"]
        self.orders = self.db["orders"]
        self.returns = self.db["returns"]
        self.notifications = self.db["notifications"]

    def verify_connection(self):
        """Sunucuya erişilemiyorsa DatabaseError fırlatır."""
        try:
            self._client.admin.command("ping")
            self._migrate_legacy_data()
            self._create_indexes()
        except PyMongoError as error:
            raise DatabaseError(
                "MongoDB sunucusuna bağlanılamadı.\n"
                "Sunucunun çalıştığından ve config.json içindeki "
                f"adresin doğru olduğundan emin olun.\n\nDetay: {error}"
            ) from error

    def _migrate_legacy_data(self):
        """Eski Türkçe koleksiyon/alan adlarını İngilizce'ye taşır."""
        existing = set(self.db.list_collection_names())
        for old_name, new_name in LEGACY_COLLECTIONS.items():
            if old_name in existing and new_name not in existing:
                self.db[old_name].rename(new_name)
        for collection_name, field_map in LEGACY_FIELDS.items():
            collection = self.db[collection_name]
            first_old_field = next(iter(field_map))
            if collection.find_one({first_old_field: {"$exists": True}}):
                # Eski alanlara ait indeksler $rename'i engeller; hepsini
                # düşür — yenileri _create_indexes içinde oluşturulur.
                collection.drop_indexes()
                collection.update_many({}, {"$rename": field_map})
        # Satış kalemlerinin içindeki alanları taşı
        for sale in self.sales.find({"items.barkod": {"$exists": True}}):
            items = [
                {LEGACY_ITEM_FIELDS.get(key, key): value
                 for key, value in item.items()}
                for item in sale.get("items", [])
            ]
            self.sales.update_one({"_id": sale["_id"]},
                                  {"$set": {"items": items}})

    def _create_indexes(self):
        self.products.create_index([("barcode", ASCENDING)], unique=True)
        self.dealers.create_index([("code", ASCENDING)], unique=True)
        self.dealers.create_index(
            [("username", ASCENDING)], unique=True,
            partialFilterExpression={"username": {"$exists": True}})
        self.sales.create_index([("date", ASCENDING)])
        self.sales.create_index([("dealer_code", ASCENDING)])
        self.dealer_stocks.create_index(
            [("dealer_code", ASCENDING), ("barcode", ASCENDING)],
            unique=True)
        self.orders.create_index([("dealer_code", ASCENDING)])
        self.orders.create_index([("created_at", ASCENDING)])
        self.orders.create_index([("status", ASCENDING)])
        self.returns.create_index([("dealer_code", ASCENDING)])
        self.returns.create_index([("created_at", ASCENDING)])
        self.notifications.create_index([("created_at", ASCENDING)])


    # ------------------------------------------------------------ Products
    def add_product(self, product: dict):
        product.setdefault("active", True)
        self.products.insert_one(product)

    def update_product(self, barcode: str, new_values: dict):
        self.products.update_one({"barcode": barcode}, {"$set": new_values})

    def delete_product(self, barcode: str):
        self.products.delete_one({"barcode": barcode})

    def get_products(self, search: str = "") -> list:
        query = {}
        if search:
            # re.escape: kullanıcı girdisiyle regex enjeksiyonunu önler
            safe = re.escape(search[:100])
            query = {
                "$or": [
                    {"name": {"$regex": safe, "$options": "i"}},
                    {"barcode": {"$regex": safe}},
                    {"box_barcode": {"$regex": safe}},
                ]
            }
        return list(self.products.find(query).sort("name", ASCENDING))

    def find_product_by_barcode(self, barcode: str):
        """Barkodu ürün ya da koli barkoduyla eşleştirir.

        Dönüş: (product, quantity_multiplier) — koli barkodu okunduysa
        çarpan ürünün box_quantity değeridir, yoksa 1'dir.
        Bulunamazsa (None, 0).
        """
        product = self.products.find_one({"barcode": barcode, "active": True})
        if product:
            return product, 1
        product = self.products.find_one(
            {"box_barcode": barcode, "active": True})
        if product:
            return product, int(product.get("box_quantity", 1) or 1)
        return None, 0

    # ------------------------------------------------------ Combined products
    def create_combined_product(self, product: dict, components: list,
                                assemble_count: int, deduct_stock: bool):
        """Bileşenlerden yeni (birleşik) ürün oluşturur.

        Önce yeni ürün eklenir (barkod çakışırsa DuplicateKeyError);
        deduct_stock True ise bileşen stokları üretim adedi kadar düşülür.
        """
        self.add_product(product)
        if deduct_stock:
            for component in components:
                self.products.update_one(
                    {"barcode": component["barcode"]},
                    {"$inc": {"stock": -component["quantity"]
                              * assemble_count}},
                )

    # ------------------------------------------------------------- Dealers
    def add_dealer(self, dealer: dict):
        dealer.setdefault("active", True)
        self.dealers.insert_one(dealer)

    def update_dealer(self, code: str, new_values: dict):
        self.dealers.update_one({"code": code}, {"$set": new_values})

    def delete_dealer(self, code: str):
        self.dealers.delete_one({"code": code})

    def get_dealers(self) -> list:
        return list(self.dealers.find().sort("code", ASCENDING))

    def remove_dealer_account(self, code: str):
        """Bayinin giriş hesabını (kullanıcı adı/parola) kaldırır."""
        self.dealers.update_one(
            {"code": code},
            {"$unset": {"username": "", "password_hash": "", "salt": ""}})

    def verify_dealer_login(self, username: str, password: str):
        """Kullanıcı adı/parola doğruysa bayi belgesini döndürür.

        Kullanıcı bulunamasa da sahte bir özet hesaplanır; böylece yanıt
        süresinden kullanıcı adı var/yok bilgisi sızmaz (zamanlama saldırısı).
        """
        dealer = self.dealers.find_one(
            {"username": str(username), "active": True})
        if not dealer or not dealer.get("password_hash"):
            _hash_password(password, secrets.token_hex(16))  # sabit süre
            return None
        expected = dealer["password_hash"]
        computed = _hash_password(password, dealer.get("salt", ""))
        if secrets.compare_digest(expected, computed):
            return dealer
        return None

    # --------------------------------------------------------------- Sales
    def save_sale(self, sale: dict):
        sale.setdefault("date", datetime.now())
        self.sales.insert_one(sale)
        # Satılan ürünlerin stoklarını düş (bayi stoğu öncelikli)
        dealer_code = sale.get("dealer_code", "")
        for item in sale.get("items", []):
            barcode = item["barcode"]
            qty = item["quantity"]
            if dealer_code:
                ds = self.dealer_stocks.find_one(
                    {"dealer_code": dealer_code, "barcode": barcode})
                if ds is not None:
                    self.dealer_stocks.update_one(
                        {"dealer_code": dealer_code, "barcode": barcode},
                        {"$inc": {"stock": -qty}})
                    continue
            self.products.update_one(
                {"barcode": barcode}, {"$inc": {"stock": -qty}})

    # ---------------------------------------------------- Dealer Stocks
    def get_dealer_stock(self, dealer_code: str, barcode: str) -> int | None:
        """Bayinin belirli ürün stok miktarını döndürür.

        Bayi için kayıt yoksa None döner (global stok kullanılır).
        """
        doc = self.dealer_stocks.find_one(
            {"dealer_code": dealer_code, "barcode": barcode})
        return int(doc["stock"]) if doc is not None else None

    def get_all_dealer_stocks(self, dealer_code: str) -> list:
        """Bayinin tüm stok kayıtlarını, ürün adıyla birleştirerek döndürür."""
        pipeline = [
            {"$match": {"dealer_code": dealer_code}},
            {"$lookup": {
                "from": "products",
                "localField": "barcode",
                "foreignField": "barcode",
                "as": "product",
            }},
            {"$addFields": {
                "name": {"$ifNull": [
                    {"$arrayElemAt": ["$product.name", 0]}, "?"
                ]},
            }},
            {"$project": {"product": 0}},
            {"$sort": {"name": 1}},
        ]
        return list(self.dealer_stocks.aggregate(pipeline))

    def set_dealer_stock(self, dealer_code: str, barcode: str, stock: int):
        """Bayinin belirli ürün stok miktarını doğrudan ayarlar."""
        self.dealer_stocks.update_one(
            {"dealer_code": dealer_code, "barcode": barcode},
            {"$set": {"stock": stock, "updated_at": datetime.now()}},
            upsert=True,
        )

    def transfer_to_dealer(self, dealer_code: str, barcode: str, qty: int):
        """Genel depodan bayi deposuna stok aktarır.

        Genel depoda yeterli stok yoksa ValueError fırlatır.
        """
        product = self.products.find_one({"barcode": barcode})
        if not product:
            raise ValueError(f"'{barcode}' barkodlu ürün bulunamadı.")
        if int(product.get("stock", 0)) < qty:
            raise ValueError(
                f"Genel depoda yeterli stok yok "
                f"(mevcut: {product.get('stock', 0)}, istenen: {qty}).")
        self.products.update_one({"barcode": barcode},
                                 {"$inc": {"stock": -qty}})
        self.dealer_stocks.update_one(
            {"dealer_code": dealer_code, "barcode": barcode},
            {"$inc": {"stock": qty},
             "$set": {"updated_at": datetime.now()}},
            upsert=True,
        )

    def get_sales(self, start: datetime = None, end: datetime = None,
                  dealer_code: str = "") -> list:
        query = {}
        if start or end:
            date_filter = {}
            if start:
                date_filter["$gte"] = start
            if end:
                date_filter["$lt"] = end
            query["date"] = date_filter
        if dealer_code:
            query["dealer_code"] = dealer_code
        return list(self.sales.find(query).sort("date", -1))

    # ---------------------------------------------------------- Statistics
    def daily_summary(self) -> dict:
        today = datetime.now().replace(hour=0, minute=0,
                                       second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        sales = self.get_sales(today, tomorrow)
        return {
            "product_count": self.products.count_documents({}),
            "dealer_count": self.dealers.count_documents({}),
            "today_sale_count": len(sales),
            "today_revenue": sum(s.get("total", 0) for s in sales),
        }

    def sales_by_day(self, days: int = 30) -> list:
        """Son N günün günlük cirosu: [(etiket, ciro, adet), ...].
        Satış olmayan günler 0 ile doldurulur."""
        today = datetime.now().replace(hour=0, minute=0,
                                       second=0, microsecond=0)
        start = today - timedelta(days=days - 1)
        pipeline = [
            {"$match": {"date": {"$gte": start}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d",
                                          "date": "$date"}},
                "total": {"$sum": "$total"},
                "count": {"$sum": 1},
            }},
        ]
        by_day = {row["_id"]: row for row in self.sales.aggregate(pipeline)}
        result = []
        for offset in range(days):
            day = start + timedelta(days=offset)
            key = day.strftime("%Y-%m-%d")
            row = by_day.get(key, {})
            result.append((day.strftime("%d.%m"),
                           float(row.get("total", 0)),
                           int(row.get("count", 0))))
        return result

    def dealer_account_summary(self, days: int = None) -> list:
        """Cari özet: bayi başına toplam ciro, satış adedi, son satış.
        Satışı olmayan bayiler de listelenir."""
        match = {}
        if days:
            start = datetime.now() - timedelta(days=days)
            match = {"date": {"$gte": start}}
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": "$dealer_code",
                "total": {"$sum": "$total"},
                "count": {"$sum": 1},
                "last_sale": {"$max": "$date"},
            }},
        ]
        by_dealer = {row["_id"]: row for row in self.sales.aggregate(pipeline)}
        result = []
        for dealer in self.get_dealers():
            row = by_dealer.get(dealer["code"], {})
            result.append({
                "code": dealer["code"],
                "name": dealer.get("name", ""),
                "total": float(row.get("total", 0)),
                "count": int(row.get("count", 0)),
                "last_sale": row.get("last_sale"),
            })
        result.sort(key=lambda r: r["total"], reverse=True)
        return result

    def payment_type_summary(self, days: int = None) -> list:
        """Ödeme türü dağılımı: [(tür, ciro, adet), ...]."""
        match = {}
        if days:
            start = datetime.now() - timedelta(days=days)
            match = {"date": {"$gte": start}}
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": "$payment_type",
                "total": {"$sum": "$total"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"total": -1}},
        ]
        return [(row["_id"] or "?", float(row["total"]), int(row["count"]))
                for row in self.sales.aggregate(pipeline)]

    # ----------------------------------------------------- Orders (Siparişler)
    def create_order(self, order: dict) -> str:
        """Yeni sipariş oluşturur; sipariş ID'sini döndürür."""
        order.setdefault("created_at", datetime.now())
        order.setdefault("status", "pending")  # pending/confirmed/shipped/delivered/cancelled
        result = self.orders.insert_one(order)
        return str(result.inserted_id)

    def get_orders(self, dealer_code: str = "", status: str = "") -> list:
        """Siparişleri filtreler ve döndürür."""
        query = {}
        if dealer_code:
            query["dealer_code"] = dealer_code
        if status:
            query["status"] = status
        return list(self.orders.find(query).sort("created_at", -1))

    def update_order_status(self, order_id, new_status: str):
        """Siparişin durumunu günceller (confirmed/shipped/delivered/cancelled)."""
        self.orders.update_one(
            {"_id": order_id},
            {"$set": {"status": new_status, "updated_at": datetime.now()}})

    def get_pending_orders_count(self) -> int:
        """Beklemede olan (pending) siparişlerin sayısı."""
        return self.orders.count_documents({"status": "pending"})

    # ---------------------------------------------------- Returns (İadeler)
    def create_return(self, return_doc: dict) -> str:
        """İade talebi oluşturur; ID döndürür."""
        return_doc.setdefault("created_at", datetime.now())
        return_doc.setdefault("status", "pending")  # pending/approved/rejected
        result = self.returns.insert_one(return_doc)
        return str(result.inserted_id)

    def get_returns(self, dealer_code: str = "", status: str = "") -> list:
        """İade taleplerini filtreler."""
        query = {}
        if dealer_code:
            query["dealer_code"] = dealer_code
        if status:
            query["status"] = status
        return list(self.returns.find(query).sort("created_at", -1))

    def update_return_status(self, return_id, new_status: str):
        """İade talebinin durumunu günceller."""
        self.returns.update_one(
            {"_id": return_id},
            {"$set": {"status": new_status, "updated_at": datetime.now()}})

    # ------------------------------------------------- Notifications (Bildirimler)
    def create_notification(self, notification: dict) -> str:
        """Bildirim oluşturur."""
        notification.setdefault("created_at", datetime.now())
        notification.setdefault("read_at", None)
        result = self.notifications.insert_one(notification)
        return str(result.inserted_id)

    def get_unread_notifications(self) -> list:
        """Okunmamış bildirimleri döndürür."""
        return list(
            self.notifications.find({"read_at": None})
            .sort("created_at", -1)
            .limit(50)
        )

    def mark_notification_read(self, notification_id):
        """Bildirimi okundu olarak işaretler."""
        self.notifications.update_one(
            {"_id": notification_id},
            {"$set": {"read_at": datetime.now()}})

    def get_unread_notification_count(self) -> int:
        """Okunmamış bildirimlerin sayısını döndürür."""
        return self.notifications.count_documents({"read_at": None})
