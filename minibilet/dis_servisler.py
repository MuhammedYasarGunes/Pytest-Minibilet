"""İnternete çıkan her şey burada: döviz kuru, ödeme ve e-posta.
Testlerde bunların hiçbiri gerçekten çalışmamalı; taklit edilmeli (mock/fake)."""
import logging
import smtplib
from decimal import Decimal
from email.message import EmailMessage

import httpx

from .hatalar import OdemeReddedildi

KUR_API = "https://api.kur.example/v1/latest"
log = logging.getLogger(__name__)


def kur_getir(para_birimi: str) -> Decimal:
    """1 birim yabancı paranın kaç TL ettiğini döndürür."""
    if para_birimi == "TRY":
        return Decimal("1")
    yanit = httpx.get(KUR_API, params={"base": para_birimi, "symbols": "TRY"}, timeout=5)
    yanit.raise_for_status()
    return Decimal(str(yanit.json()["rates"]["TRY"]))


class OdemeIstemcisi:
    """Ödeme sağlayıcısının REST API'si ile konuşur."""

    def __init__(self, taban_url: str, api_anahtari: str, http: httpx.Client | None = None):
        self.http = http or httpx.Client(base_url=taban_url, timeout=10,
                                         headers={"Authorization": f"Bearer {api_anahtari}"})

    def tahsil_et(self, tutar: Decimal, eposta: str) -> str:
        yanit = self.http.post("/odemeler", json={"tutar": str(tutar), "eposta": eposta})
        if yanit.status_code == 402:
            raise OdemeReddedildi(yanit.json().get("neden", "Ödeme reddedildi"))
        yanit.raise_for_status()
        return yanit.json()["odeme_no"]

    def iade_et(self, odeme_no: str) -> None:
        self.http.post(f"/odemeler/{odeme_no}/iade").raise_for_status()


class SmtpBildirimci:
    """Gerçek e-posta gönderir. Testlerde yerine sahte (fake) bir bildirimci kullan."""

    def __init__(self, sunucu: str, gonderen: str):
        self.sunucu, self.gonderen = sunucu, gonderen

    def gonder(self, alici: str, konu: str, metin: str) -> None:
        mesaj = EmailMessage()
        mesaj["From"], mesaj["To"], mesaj["Subject"] = self.gonderen, alici, konu
        mesaj.set_content(metin)
        with smtplib.SMTP(self.sunucu) as smtp:
            smtp.send_message(mesaj)
