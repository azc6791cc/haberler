"""Aday besleme adreslerine canlı test.

DÜZELTMELER (önceki ölçüm hataları):
  - Kanal seviyesindeki <channel><pubDate> haber tarihi DEĞİLDİR; tazelik yalnızca
    item/entry içindeki tarihlerin en yenisinden ölçülür.
  - Gövde ASLA kırpılmaz; kırpma CDATA'yı yarıda bırakıp sahte ParseError üretir.

Kullanım:
  python tests/check_feeds.py         -> aday listesinin tamamı
  python tests/check_feeds.py eleme   -> BirGün + TechTurco derin doğrulama
"""
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SURE = 15
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

URLS = [
    "https://www.sozcu.com.tr/feeds-son-dakika",
    "https://www.ahaber.com.tr/rss/news.xml",
    "https://artigercek.com/export/rss",
    "https://www.aydinlik.com.tr/feed",
    "https://feeds.bbci.co.uk/turkce/rss.xml",
    "https://www.birgun.net/rss/home",
    "https://www.cnnturk.com/feed/rss/guncel/news",
    "https://tr.euronews.com/rss",
    "https://www.evrensel.net/rss/haber.xml",
    "https://www.gazeteduvar.com.tr/export/rss",
    "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr",
    "https://www.haberturk.com/rss",
    "https://halktv.com.tr/export/rss",
    "https://www.internethaber.com/rss",
    "https://www.korkusuz.com.tr/feeds/rss",
    "https://www.milliyet.com.tr/rss/rssnew/sondakikarss.xml",
    "https://www.mynet.com/haber/rss/sondakika",
    "https://www.odatv.com/rss.xml",
    "https://www.techturco.com/rss",
    "https://www.teknolojioku.com/export/rss",
    "https://www.fotomac.com.tr/rss/son24saat.xml",
    "https://www.timeturk.com/rss/feed",
]

BASLIKLAR = ("pubDate", "published", "updated", "date")
def ayrıştır(ham):
    """RFC 822 / ISO 8601 tarih metnini datetime'a çevirir; olmazsa None."""
    try:
        return parsedate_to_datetime(ham)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(ham.replace("Z", "+00:00"))
    except Exception:
        pass
    for bicim in ("%a, %d %b %y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %z",
                  "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ham, bicim)
        except Exception:
            continue
    return None


def indir(url):
    """Feed gövdesini TAMAMEN indirir (kırpma yok) veya (None, hata) döner."""
    istek = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "application/rss+xml,application/xml,text/xml,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(istek, timeout=SURE, context=ctx) as y:
            return y.read(), (y.headers.get("Content-Type") or "").split(";")[0]
    except urllib.error.HTTPError as e:
        return None, f"HTTP-{e.code}"
    except Exception as e:
        return None, f"HATA:{type(e).__name__}"


def ogeleri_ayikla(kok):
    return kok.findall(".//item") or kok.findall(".//{http://www.w3.org/2005/Atom}entry")


def tarihleri_ayikla(ogeler):
    """[(datetime, ham_metin, baslik, saat_once)] — yalnızca item/entry içinden."""
    simdi = datetime.now(timezone.utc)
    cikti = []
    for el in ogeler:
        ham = ""
        for cocuk in el:
            if cocuk.tag.split("}")[-1] in BASLIKLAR and (cocuk.text or "").strip():
                ham = cocuk.text.strip()
                break
        baslik = (el.findtext("title") or "").strip()[:58]
        t = ayrıştır(ham) if ham else None
        if t is None:
            continue
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        cikti.append((t, ham, baslik, (simdi - t).total_seconds() / 3600))
    return cikti


def kontrol(url):
    veri, ct = indir(url)
    if veri is None:
        return ct, 0, "-"
    rss_mu = ("xml" in ct.lower()) or veri[:300].lstrip().startswith(b"<?xml")
    try:
        kok = ET.fromstring(veri)
    except Exception:
        return ("OK" if rss_mu else "RSS-DEGIL"), -1, "PARSE-HATASI"
    ogeler = ogeleri_ayikla(kok)
    ts = tarihleri_ayikla(ogeler)
    if not ts:
        return ("OK" if rss_mu else "RSS-DEGIL"), len(ogeler), "item-tarihi-yok"
    en = max(ts, key=lambda x: x[0])
    return ("OK" if rss_mu else "RSS-DEGIL"), len(ogeler), \
        f"{en[1][:30]} ({en[3]:.1f} saat once)"


def eleme_dogrula():
    """BirGün ve TechTurco: tam veri ile derin doğrulama."""
    satirlar = []
    for url in ("https://www.birgun.net/rss/home", "https://www.techturco.com/rss"):
        satirlar.append(f"\n=== {url}")
        veri, ct = indir(url)
        if veri is None:
            satirlar.append(f"INDIRME HATASI: {ct}")
            continue
        satirlar.append(f"tam_boyut={len(veri)} bayt, Content-Type={ct}")
        try:
            kok = ET.fromstring(veri)
        except Exception as e:
            satirlar.append(f"PARSE HATASI (tam veri): {type(e).__name__}: {e}")
            continue
        ogeler = ogeleri_ayikla(kok)
        ts = tarihleri_ayikla(ogeler)
        satirlar.append(f"PARSE TAMAM  ->  item={len(ogeler)}, tarihli={len(ts)}")
        satirlar.append("EN YENI 10 HABER:")
        for _, ham, baslik, saat in sorted(ts, key=lambda x: x[0], reverse=True)[:10]:
            satirlar.append(f"  {saat:7.1f} saat | {ham[:31]:<31} | {baslik}")
        if ts:
            satirlar.append(f"-> EN TAZE: {max(ts, key=lambda x: x[0])[3]:.1f} saat once")
    with open("tests/eleme-raporu.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "eleme":
        return eleme_dogrula()
    satirlar = [
        "=" * 122,
        "{:<4} {:<10} {:<28} {:<6} {:<42} {}".format(
            "SN", "DURUM", "CONTENT-TYPE", "ITEM", "EN TAZE HABER TARIHI", "URL"),
        "=" * 122,
    ]
    calisan = 0
    for i, url in enumerate(URLS, 1):
        durum, adet, tarih = kontrol(url)
        if durum == "OK" and adet > 0:
            calisan += 1
        satirlar.append("{:<4} {:<10} {:<28} {:<6} {:<42} {}".format(
            i, durum, adet if adet >= 0 else "-", tarih, url))
    satirlar.append("")
    satirlar.append(f"KULLANILABILIR: {calisan}/{len(URLS)}")
    with open("tests/aday-raporu.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


if __name__ == "__main__":
    main()