"""MiniBilet'in kendi hata sınıfları. Her biri API'de bir HTTP durum koduna karşılık gelir."""


class MiniBiletHatasi(Exception):
    durum_kodu = 400


class BulunamadiHatasi(MiniBiletHatasi):
    durum_kodu = 404


class GecersizKupon(MiniBiletHatasi):
    durum_kodu = 400


class KontenjanDolu(MiniBiletHatasi):
    durum_kodu = 409


class EtkinlikGecti(MiniBiletHatasi):
    durum_kodu = 409


class ZatenIptal(MiniBiletHatasi):
    durum_kodu = 409


class OdemeReddedildi(MiniBiletHatasi):
    durum_kodu = 402
