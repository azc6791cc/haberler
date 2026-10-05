#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_data klasörünü günceller.

Amaç: `python bot.py --fixture tests/test_data` ağsız çalışabilsin.
Yöntem: sources.json'daki HER beslemeyi canlıdan indirip doğru dosya adıyla
        tests/test_data altına yazar; kaynak listesinde olmayan eski dosyaları siler.

Kullanım:
  python tests/fetch_fixtures.py            # tümünü indir
  python tests/fetch_fixtures.py hurriyet   # yalnız eşleşen kaynaklar

Not: bot.py'nin --fixture modu dosya adını şu kuralla üretir:
    url.lower() -> [^a-z0-9]+ -> "_" -> ilk 80 karakter
"""
import concurrent.futures
import json
import os
import re
import ssl
import sys
import urllib.request
import xml.etree.ElementTree as ET

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEDEF = os.path.join(KOK, "tests", "test_data")
ZAMAN_ASIMI = 25
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def dosya_adi(url):
    """bot.py besleme_cek() ile birebir aynı adlandırma."""
    ad = re.sub(r"[^a-z0-9]+", "_", url.lower()).strip("_")[:80]
    return ad + ".xml"


def indir(besleme):
    url = besleme["url"]
    istek = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "application/rss+xml,application/xml,text/xml,*/*;q=0.8",
    })
    try:
        with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI, context=ctx) as y:
            veri = y.read(1500000)
    except Exception as e:
        return url, None, f"{type(e).__name__}"
    try:
        kok = ET.fromstring(veri)
        adet = len(kok.findall(".//item")) or len(
            kok.findall(".//{http://www.w3.org/2005/Atom}entry"))
    except Exception:
        return url, None, "PARSE-EDILEMEDI"
    if not adet:
        return url, None, "0-item"
    with open(os.path.join(HEDEF, dosya_adi(url)), "wb") as f:
        f.write(veri)
    return url, adet, None


def main():
    with open(os.path.join(KOK, "sources.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(HEDEF, exist_ok=True)

    filtre = sys.argv[1] if len(sys.argv) > 1 else ""
    beklenen = set()
    isler = []
    for kaynak in cfg["kaynaklar"]:
        if filtre and filtre not in kaynak["id"]:
            continue
        for b in kaynak["beslemeler"]:
            beklenen.add(dosya_adi(b["url"]))
            isler.append(b)

    print(f"{len(isler)} besleme indiriliyor...")
    tamam, hatali = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as havuz:
        for url, adet, hata in havuz.map(indir, isler):
            if hata:
                hatali.append((url, hata))
            else:
                tamam.append((url, adet))

    if not filtre:
        silinen = []
        for ad in os.listdir(HEDEF):
            if ad not in beklenen:
                os.remove(os.path.join(HEDEF, ad))
                silinen.append(ad)

    print(f"\nBASARILI: {len(tamam)}")
    for u, a in sorted(tamam):
        print(f"  {a:>4} item  {u}")
    if hatali:
        print(f"\nBASARISIZ: {len(hatali)}")
        for u, h in sorted(hatali):
            print(f"  {h:<18} {u}")
    if not filtre:
        print(f"\nSILINEN ESKI DOSYA: {len(silinen)}")
        for a in sorted(silinen):
            print("  - " + a)


if __name__ == "__main__":
    main()