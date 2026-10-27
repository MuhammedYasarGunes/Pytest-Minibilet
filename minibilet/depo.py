"""SQLite tabanlı veri katmanı. Testlerde ":memory:" ya da geçici bir dosya kullanılabilir."""
import sqlite3
from datetime import datetime
from decimal import Decimal

from .hatalar import BulunamadiHatasi
from .modeller import Etkinlik, Rezervasyon

SEMA = """
CREATE TABLE IF NOT EXISTS etkinlik (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL,
    tarih TEXT NOT NULL,
    kontenjan INTEGER NOT NULL CHECK (kontenjan > 0),
    birim_fiyat TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rezervasyon (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etkinlik_id INTEGER NOT NULL REFERENCES etkinlik(id),
    eposta TEXT NOT NULL,
    adet INTEGER NOT NULL,
    tutar TEXT NOT NULL,
    odeme_no TEXT NOT NULL,
    durum TEXT NOT NULL DEFAULT 'aktif',
    olusturma TEXT NOT NULL
);
"""


class Depo:
    def __init__(self, yol: str = ":memory:"):
        self.db = sqlite3.connect(yol, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SEMA)

    def kapat(self) -> None:
        self.db.close()

    # --- etkinlik ---
    def etkinlik_ekle(self, ad: str, tarih: datetime, kontenjan: int, birim_fiyat) -> Etkinlik:
        imlec = self.db.execute(
            "INSERT INTO etkinlik (ad, tarih, kontenjan, birim_fiyat) VALUES (?, ?, ?, ?)",
            (ad, tarih.isoformat(), kontenjan, str(Decimal(str(birim_fiyat)))),
        )
        self.db.commit()
        return self.etkinlik_getir(imlec.lastrowid)

    def etkinlik_getir(self, etkinlik_id: int) -> Etkinlik:
        satir = self.db.execute("SELECT * FROM etkinlik WHERE id = ?", (etkinlik_id,)).fetchone()
        if satir is None:
            raise BulunamadiHatasi(f"Etkinlik bulunamadı: {etkinlik_id}")
        return self._etkinlik(satir)

    def etkinlikler(self) -> list[Etkinlik]:
        return [self._etkinlik(s) for s in self.db.execute("SELECT * FROM etkinlik ORDER BY tarih")]

    def satilan_adet(self, etkinlik_id: int) -> int:
        satir = self.db.execute(
            "SELECT COALESCE(SUM(adet), 0) FROM rezervasyon WHERE etkinlik_id = ? AND durum = 'aktif'",
            (etkinlik_id,),
        ).fetchone()
        return satir[0]

    # --- rezervasyon ---
    def rezervasyon_ekle(self, etkinlik_id: int, eposta: str, adet: int, tutar: Decimal,
                         odeme_no: str, olusturma: datetime) -> Rezervasyon:
        imlec = self.db.execute(
            "INSERT INTO rezervasyon (etkinlik_id, eposta, adet, tutar, odeme_no, olusturma) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (etkinlik_id, eposta, adet, str(tutar), odeme_no, olusturma.isoformat()),
        )
        self.db.commit()
        return self.rezervasyon_getir(imlec.lastrowid)

    def rezervasyon_getir(self, rezervasyon_id: int) -> Rezervasyon:
        satir = self.db.execute("SELECT * FROM rezervasyon WHERE id = ?", (rezervasyon_id,)).fetchone()
        if satir is None:
            raise BulunamadiHatasi(f"Rezervasyon bulunamadı: {rezervasyon_id}")
        return Rezervasyon(
            id=satir["id"], etkinlik_id=satir["etkinlik_id"], eposta=satir["eposta"], adet=satir["adet"],
            tutar=Decimal(satir["tutar"]), odeme_no=satir["odeme_no"], durum=satir["durum"],
            olusturma=datetime.fromisoformat(satir["olusturma"]),
        )

    def rezervasyonlar(self, etkinlik_id: int) -> list[Rezervasyon]:
        ids = self.db.execute("SELECT id FROM rezervasyon WHERE etkinlik_id = ? ORDER BY id", (etkinlik_id,))
        return [self.rezervasyon_getir(s["id"]) for s in ids]

    def rezervasyon_iptal(self, rezervasyon_id: int) -> None:
        self.db.execute("UPDATE rezervasyon SET durum = 'iptal' WHERE id = ?", (rezervasyon_id,))
        self.db.commit()

    @staticmethod
    def _etkinlik(satir) -> Etkinlik:
        return Etkinlik(id=satir["id"], ad=satir["ad"], tarih=datetime.fromisoformat(satir["tarih"]),
                        kontenjan=satir["kontenjan"], birim_fiyat=Decimal(satir["birim_fiyat"]))
