"""SKT ve stok uyarıları sistemi."""
from datetime import date, timedelta


def get_expiry_alerts(db, warning_days: int = 30) -> dict:
    """
    SKT yaklaşan ve geçmiş ürünleri bulur.
    
    Dönüş: {
        "expired": [(product, days_late), ...],
        "expiring_soon": [(product, days_left), ...],
    }
    """
    today = date.today()
    products = db.get_products("")
    
    expired = []
    expiring_soon = []
    
    for product in products:
        expiry = product.get("expiry_date")
        if not expiry:
            continue
        
        from datetime import datetime
        if isinstance(expiry, datetime):
            expiry = expiry.date()
        
        days_diff = (expiry - today).days
        
        if days_diff < 0:
            expired.append((product, -days_diff))
        elif days_diff <= warning_days:
            expiring_soon.append((product, days_diff))
    
    return {
        "expired": sorted(expired, key=lambda x: x[1], reverse=True),
        "expiring_soon": sorted(expiring_soon, key=lambda x: x[1]),
    }


def format_expiry_report(alerts: dict) -> str:
    """Uyarı raporunu metin olarak formatla."""
    lines = []
    
    if alerts["expired"]:
        lines.append("⚠️  GEÇMİŞ SKT ÜRÜNLER:")
        for product, days in alerts["expired"]:
            lines.append(
                f"  • {product['name']} ({product['barcode']}) — "
                f"{days} gün geçmiş")
    
    if alerts["expiring_soon"]:
        lines.append("\n⏰ YAKLAŞAN SKT ÜRÜNLER:")
        for product, days in alerts["expiring_soon"]:
            lines.append(
                f"  • {product['name']} ({product['barcode']}) — "
                f"{days} gün kaldı")
    
    return "\n".join(lines) if lines else "SKT uyarısı yok ✓"
