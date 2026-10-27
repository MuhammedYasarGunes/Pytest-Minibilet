"""FastAPI uygulaması. Çalıştırmak için: uvicorn minibilet.api:app --reload"""
import os
from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .depo import Depo
from .dis_servisler import OdemeIstemcisi, SmtpBildirimci
from .hatalar import MiniBiletHatasi
from .servis import RezervasyonServisi

app = FastAPI(title="MiniBilet")


@app.exception_handler(MiniBiletHatasi)
async def hata_yanitla(request: Request, hata: MiniBiletHatasi):
    return JSONResponse(status_code=hata.durum_kodu, content={"hata": type(hata).__name__, "mesaj": str(hata)})


# --- bağımlılıklar: testlerde app.dependency_overrides ile değiştirilir ---
def get_depo():
    depo = Depo(os.environ.get("MINIBILET_DB", "minibilet.db"))
    try:
        yield depo
    finally:
        depo.kapat()


def get_servis(depo: Depo = Depends(get_depo)) -> RezervasyonServisi:
    odeme = OdemeIstemcisi(os.environ.get("ODEME_URL", "https://odeme.example"), os.environ.get("ODEME_ANAHTARI", ""))
    bildirimci = SmtpBildirimci(os.environ.get("SMTP_SUNUCU", "localhost"), "bilet@minibilet.example")
    return RezervasyonServisi(depo, odeme, bildirimci)


# --- şemalar ---
class EtkinlikGirdi(BaseModel):
    ad: str = Field(min_length=3, max_length=100)
    tarih: datetime
    kontenjan: int = Field(gt=0, le=10_000)
    birim_fiyat: Decimal = Field(gt=0)


class RezervasyonGirdi(BaseModel):
    eposta: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    adet: int = Field(ge=1, le=10)
    ogrenci: bool = False
    kupon: str | None = None


def etkinlik_json(e, depo: Depo) -> dict:
    return {"id": e.id, "ad": e.ad, "tarih": e.tarih.isoformat(), "kontenjan": e.kontenjan,
            "kalan": e.kontenjan - depo.satilan_adet(e.id), "birim_fiyat": str(e.birim_fiyat)}


# --- uç noktalar ---
@app.get("/saglik")
async def saglik():
    return {"durum": "ok"}


@app.get("/etkinlikler")
def etkinlikleri_listele(depo: Depo = Depends(get_depo)):
    return [etkinlik_json(e, depo) for e in depo.etkinlikler()]


@app.post("/etkinlikler", status_code=201)
def etkinlik_olustur(girdi: EtkinlikGirdi, depo: Depo = Depends(get_depo)):
    e = depo.etkinlik_ekle(girdi.ad, girdi.tarih, girdi.kontenjan, girdi.birim_fiyat)
    return etkinlik_json(e, depo)


@app.get("/etkinlikler/{etkinlik_id}")
def etkinlik_getir(etkinlik_id: int, depo: Depo = Depends(get_depo)):
    return etkinlik_json(depo.etkinlik_getir(etkinlik_id), depo)


@app.get("/etkinlikler/{etkinlik_id}/teklif")
def fiyat_teklifi(etkinlik_id: int, adet: int = Query(ge=1, le=10), para_birimi: str = "TRY",
                  servis: RezervasyonServisi = Depends(get_servis)):
    return {"tutar": str(servis.fiyat_teklifi(etkinlik_id, adet, para_birimi)), "para_birimi": para_birimi}


@app.post("/etkinlikler/{etkinlik_id}/rezervasyonlar", status_code=201)
def rezervasyon_yap(etkinlik_id: int, girdi: RezervasyonGirdi,
                    servis: RezervasyonServisi = Depends(get_servis)):
    r = servis.rezerve_et(etkinlik_id, girdi.eposta, girdi.adet, girdi.ogrenci, girdi.kupon)
    return {"id": r.id, "adet": r.adet, "tutar": str(r.tutar), "durum": r.durum}


@app.delete("/rezervasyonlar/{rezervasyon_id}")
def rezervasyon_iptal(rezervasyon_id: int, servis: RezervasyonServisi = Depends(get_servis)):
    return {"iade": str(servis.iptal_et(rezervasyon_id))}
