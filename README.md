# MiniBilet

pytest öğrenmek için hazırlanmış küçük bir **etkinlik bileti** servisi (FastAPI + SQLite).
Uygulama kodu hazır; **testlerin hiçbiri yazılmadı**. Testleri sen yazacaksın.

> Kodda README'deki kurallara uymayan **3 bilinçli hata** var. İyi testler onları bulur.
> Hangi oturumda bulacağın plan PDF'inde yazıyor; yerlerini önceden arama.

## Kurulum

```bash
cd minibilet
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
pytest            # henüz test yok: "no tests ran" görmen normal
uvicorn minibilet.api:app --reload   # isteğe bağlı: http://127.0.0.1:8000/docs
```

## Klasör yapısı

| Dosya | Ne yapar | Hangi oturumda test edilir |
|---|---|---|
| `minibilet/fiyat.py` | İndirim ve toplam fiyat hesabı (saf fonksiyonlar) | O1, O2, O9 |
| `minibilet/depo.py` | SQLite veri katmanı | O3, O4 |
| `minibilet/servis.py` | Rezervasyon, iptal ve teklif iş kuralları | O4, O5, O8 |
| `minibilet/dis_servisler.py` | Döviz kuru, ödeme ve e-posta (internete çıkar) | O5 |
| `minibilet/api.py` | FastAPI uç noktaları | O6 |
| `minibilet/hatalar.py` | Hata sınıfları ve HTTP durum kodları | her yerde |

## İş kuralları (testlerin doğruluk kaynağı)

### Fiyat

| Kural | Ayrıntı |
|---|---|
| Adet | Bir rezervasyonda **1 ile 10** bilet. Dışı `ValueError`. |
| Birim fiyat | Pozitif olmalı, değilse `ValueError`. |
| Öğrenci indirimi | %20 |
| Grup indirimi | **5 ve üzeri** bilette %15 |
| Kupon | `HOSGELDIN` %10, `FIRAT2026` %15. Kupon kodları **büyük/küçük harf duyarsızdır**, baştaki ve sondaki boşluklar yok sayılır. Tanımsız kupon `GecersizKupon`. |
| Erken kayıt | Etkinliğe **30 gün veya daha fazla** varsa %10 |
| Üst sınır | İndirimler toplanır ama toplam indirim **en fazla %40** olur. |
| Yuvarlama | Sonuç kuruşa yuvarlanır (yarım kuruş yukarı). |

### Rezervasyon

- Tarihi geçmiş (ya da şu an başlayan) etkinliğe rezervasyon yapılamaz: `EtkinlikGecti` (409).
- Kalan kontenjandan fazla bilet istenemez: `KontenjanDolu` (409). İptal edilen biletler kontenjana geri döner.
- Önce ödeme alınır. Ödeme reddedilirse (`OdemeReddedildi`, 402) **hiçbir kayıt oluşmaz**.
- Ödemeden sonra onay e-postası gönderilir. E-posta gitmese bile rezervasyon geçerlidir; sadece uyarı loglanır.

### İptal

- Etkinliğe **48 saat veya daha fazla** varken iptal edilirse ödenen tutarın tamamı iade edilir.
- 48 saatten az kala iptalde iade yoktur (0 TL), ama rezervasyon yine iptal edilir.
- Zaten iptal edilmiş rezervasyon tekrar iptal edilemez: `ZatenIptal` (409).

### Fiyat teklifi

- `/etkinlikler/{id}/teklif?adet=2&para_birimi=EUR` toplamı istenen para biriminde verir.
  TL tutar, döviz kuru servisinden alınan kura bölünür ve kuruşa yuvarlanır.

## Yapılacaklar (O8'de TDD ile)

- [ ] Aynı e-posta, aynı etkinlik için **ikinci aktif rezervasyonu** yapamaz: `MukerrerRezervasyon` (409).
  İptal edilmiş eski rezervasyon engel değildir.
