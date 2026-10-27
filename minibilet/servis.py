"""İş kuralları: rezervasyon yapma, iptal ve fiyat teklifi."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from .depo import Depo
from .dis_servisler import kur_getir
from .fiyat import kurusa_yuvarla, toplam_fiyat
from .hatalar import EtkinlikGecti, KontenjanDolu, ZatenIptal
from .modeller import Rezervasyon

IADE_SINIRI = timedelta(hours=48)
log = logging.getLogger(__name__)


class RezervasyonServisi:
    def __init__(self, depo: Depo, odeme, bildirimci, saat=datetime.now):
        self.depo = depo
        self.odeme = odeme
        self.bildirimci = bildirimci
        self.saat = saat  # testlerde sabit bir saat verilebilir

    def rezerve_et(self, etkinlik_id: int, eposta: str, adet: int,
                   ogrenci: bool = False, kupon: str | None = None) -> Rezervasyon:
        etkinlik = self.depo.etkinlik_getir(etkinlik_id)
        simdi = self.saat()
        if etkinlik.tarih <= simdi:
            raise EtkinlikGecti("Etkinlik tarihi geçmiş")

        kalan = etkinlik.kontenjan - self.depo.satilan_adet(etkinlik_id)
        if adet > kalan:
            raise KontenjanDolu(f"Yalnızca {kalan} yer kaldı")

        tutar = toplam_fiyat(etkinlik.birim_fiyat, adet, ogrenci=ogrenci, kupon=kupon,
                             bugun=simdi.date(), etkinlik_tarihi=etkinlik.tarih.date())
        odeme_no = self.odeme.tahsil_et(tutar, eposta)  # reddedilirse hiçbir şey kaydedilmez
        rezervasyon = self.depo.rezervasyon_ekle(etkinlik_id, eposta, adet, tutar, odeme_no, simdi)

        try:
            self.bildirimci.gonder(eposta, f"{etkinlik.ad}: rezervasyonun onaylandı",
                                   f"{adet} bilet, toplam {tutar} TL. Rezervasyon no: {rezervasyon.id}")
        except Exception:  # e-posta gitmese de rezervasyon geçerli kalır
            log.warning("Onay e-postası gönderilemedi: %s", eposta)
        return rezervasyon

    def iptal_et(self, rezervasyon_id: int) -> Decimal:
        """Rezervasyonu iptal eder ve iade edilen tutarı döndürür."""
        rezervasyon = self.depo.rezervasyon_getir(rezervasyon_id)
        if rezervasyon.durum == "iptal":
            raise ZatenIptal("Rezervasyon zaten iptal edilmiş")
        etkinlik = self.depo.etkinlik_getir(rezervasyon.etkinlik_id)

        if etkinlik.tarih - self.saat() > IADE_SINIRI:
            self.odeme.iade_et(rezervasyon.odeme_no)
            iade = rezervasyon.tutar
        else:
            iade = Decimal("0")
        self.depo.rezervasyon_iptal(rezervasyon_id)
        return iade

    def fiyat_teklifi(self, etkinlik_id: int, adet: int, para_birimi: str = "TRY", **indirim) -> Decimal:
        etkinlik = self.depo.etkinlik_getir(etkinlik_id)
        simdi = self.saat()
        tl = toplam_fiyat(etkinlik.birim_fiyat, adet, bugun=simdi.date(),
                          etkinlik_tarihi=etkinlik.tarih.date(), **indirim)
        return kurusa_yuvarla(tl / kur_getir(para_birimi))
