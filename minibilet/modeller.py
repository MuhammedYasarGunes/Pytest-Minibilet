from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Etkinlik:
    id: int
    ad: str
    tarih: datetime
    kontenjan: int
    birim_fiyat: Decimal


@dataclass(frozen=True)
class Rezervasyon:
    id: int
    etkinlik_id: int
    eposta: str
    adet: int
    tutar: Decimal
    odeme_no: str
    durum: str  # "aktif" veya "iptal"
    olusturma: datetime
