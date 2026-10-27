"""Bilet fiyat kuralları. Kuralların doğrusu README'deki tablodadır."""
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .hatalar import GecersizKupon

KUPONLAR = {"HOSGELDIN": Decimal("0.10"), "FIRAT2026": Decimal("0.15")}
OGRENCI_INDIRIMI = Decimal("0.20")
GRUP_ESIGI = 5
GRUP_INDIRIMI = Decimal("0.15")
ERKEN_KAYIT_GUN = 30
ERKEN_KAYIT_INDIRIMI = Decimal("0.10")
EN_FAZLA_INDIRIM = Decimal("0.40")
EN_FAZLA_ADET = 10


def kurusa_yuvarla(tutar: Decimal) -> Decimal:
    return tutar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def indirim_orani(adet: int, ogrenci: bool = False, kupon: str | None = None,
                  bugun: date | None = None, etkinlik_tarihi: date | None = None) -> Decimal:
    """Uygulanacak toplam indirim oranını döndürür (0.00 ile 0.40 arası)."""
    oran = Decimal("0")
    if ogrenci:
        oran += OGRENCI_INDIRIMI
    if adet > GRUP_ESIGI:
        oran += GRUP_INDIRIMI
    if kupon:
        if kupon not in KUPONLAR:
            raise GecersizKupon(f"Geçersiz kupon: {kupon}")
        oran += KUPONLAR[kupon]
    if bugun and etkinlik_tarihi and (etkinlik_tarihi - bugun).days >= ERKEN_KAYIT_GUN:
        oran += ERKEN_KAYIT_INDIRIMI
    return min(oran, EN_FAZLA_INDIRIM)


def toplam_fiyat(birim_fiyat, adet: int, **indirim_bilgisi) -> Decimal:
    """Birim fiyat x adet, indirimler uygulanmış ve kuruşa yuvarlanmış."""
    birim = Decimal(str(birim_fiyat))
    if birim <= 0:
        raise ValueError("Birim fiyat pozitif olmalı")
    if not 1 <= adet <= EN_FAZLA_ADET:
        raise ValueError(f"Adet 1 ile {EN_FAZLA_ADET} arasında olmalı")
    oran = indirim_orani(adet, **indirim_bilgisi)
    return kurusa_yuvarla(birim * adet * (1 - oran))
