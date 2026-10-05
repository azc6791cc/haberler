#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mükerrer haber ölçümü. haberler.json üzerinde farklı eşik stratejilerini deneyip
gerçekten aynı olan haberleri bulur. Çıktı: tests/mukerrer-raporu.txt
"""
import json
import re
from datetime import datetime, timedelta
from itertools import combinations

RE_WS = re.compile(r"\s+")
STOP = {
    "haber", "haberi", "haberde", "haberin", "yer", "olan", "olanlar", "gundem",
    "son", "dakika", "icinde", "uzerinde", "sonrasi", "icin", "ile", "veya",
    "kadar", "daha", "cok", "var", "yok", "bir", "iki", "bu", "su", "da", "de",
    "ne", "nasil", "kim", "mı", "mi", "mu", "mu", "aciklama", "paylas",
}


def norm_baslik(baslik):
    if not baslik:
        return ""
    b = baslik.casefold().replace("\u0069\u0307", "i")
    b = re.sub(r"[\u200b\ufeff\u0307]", "", b)
    b = b.replace("'", "").replace("\u2019", "").replace("\u0060", "")
    for k, v in [("ı", "i"), ("ğ", "g"), ("ü", "u"), ("ş", "s"),
                 ("ö", "o"), ("ç", "c")]:
        b = b.replace(k, v)
    return RE_WS.sub(" ", re.sub(r"[^a-z0-9]+", " ", b)).strip()


def kelimeler(metin):
    return {w for w in norm_baslik(metin).split() if len(w) >= 4 and w not in STOP}


def alan_adi(link):
    parcalar = link.split("/")
    return re.sub(r"^www\.", "", parcalar[2]) if len(parcalar) > 2 else link


def jaccard(a, b):
    if not a or not b:
        return 0.0
    kesisim = len(a & b)
    return kesisim / len(a | b)


def ornekler(kayit, esik_baslik, esik_aciklama, pencere_saat=12):
    """Esikleri gecen ciftlerin GERCEK basliklarini dump eder (yanlis eleme kontrolu)."""
    n = len(kayit)
    pencere = timedelta(hours=pencere_saat)
    baslik_cift, aciklama_cift = [], []
    for i, j in combinations(range(n), 2):
        a, b = kayit[i], kayit[j]
        if a["kaynak"] == b["kaynak"]:
            continue
        if abs(a["tarih"] - b["tarih"]) > pencere:
            continue
        jb = jaccard(a["kb"], b["kb"])
        ja = jaccard(a["ka"], b["ka"])
        if jb >= esik_baslik:
            baslik_cift.append((jb, ja, a, b))
        if ja >= esik_aciklama:
            aciklama_cift.append((ja, a, b))

    c = ["", "=" * 110,
         f"BASLIK JACCARD >= {esik_baslik}  ->  {len(baslik_cift)} cift",
         "=" * 110]
    for jb, ja, a, b in sorted(baslik_cift, key=lambda x: -x[0]):
        c.append(f"baslik={jb:.2f} aciklama={ja:.2f}  ({a['kaynak']} ~ {b['kaynak']})")
        c.append(f"   A: {a['baslik'][:105]}")
        c.append(f"   B: {b['baslik'][:105]}")

    c += ["", "=" * 110,
          f"ACIKLAMA JACCARD >= {esik_aciklama}  ->  {len(aciklama_cift)} cift",
          "=" * 110]
    for ja, a, b in sorted(aciklama_cift, key=lambda x: -x[0]):
        c.append(f"aciklama={ja:.2f}  ({a['kaynak']} ~ {b['kaynak']})")
        c.append(f"   A: {a['baslik'][:105]}")
        c.append(f"   B: {b['baslik'][:105]}")
    return c


def elenenleri_goster(cikti):
    """Çıktıdaki mükerrer kalmadığını doğrular: aynı konudan kaç haber var?"""
    from collections import defaultdict
    with open(cikti, encoding="utf-8") as f:
        hab = json.load(f)
    gruplar = defaultdict(list)
    for h in hab:
        gruplar[norm_baslik(h["baslik"])].append(h)
    tek = {k: v for k, v in gruplar.items() if len(v) > 1}

    c = [f"Girdi: {cikti}  ({len(hab)} haber)", "",
         f"Ayni normalize basliga sahip grup sayisi: {len(tek)}"]
    for k, v in tek.items():
        c.append(f"  [{len(v)}x] {v[0]['baslik'][:95]}")
        for h in v:
            alan = re.sub(r"^www\.", "", h["link"].split("/")[2])
            c.append(f"        - {alan}")

    c += ["", "=" * 100, "YAKIN KONU KONTROLU (eleme olmadıysa da aynı olaydan kaç haber var?)",
          "=" * 100]
    for anahtar in ("serdal adali", "fransa lise", "teknofest", "adin a deprem",
                    "fenerbahce tarfin", "yemen", "teknoloji oku"):
        es = [h for h in hab if anahtar in norm_baslik(h["baslik"])]
        c.append(f"\n'{anahtar}' -> {len(es)} haber")
        for h in es:
            alan = re.sub(r"^www\.", "", h["link"].split("/")[2])
            c.append(f"   {alan:<28} {h['baslik'][:80]}")
    return c


def main():
    with open("haberler.json", encoding="utf-8") as f:
        haberler = json.load(f)
    n = len(haberler)
    satirlar = [f"Toplam haber: {n}\n"]

    # Hazırlık
    kayit = []
    for h in haberler:
        try:
            t = datetime.fromisoformat(h["tarih"])
        except Exception:
            t = datetime.now()
        kayit.append({
            "baslik": h["baslik"],
            "link": h["link"],
            "kaynak": alan_adi(h["link"]),
            "tarih": t,
            "nb": norm_baslik(h["baslik"]),
            "kb": kelimeler(h["baslik"]),
            "ka": kelimeler(h.get("aciklama", "")),
        })

    # 0) Şu anki durum: tam başlık+link
    tam = {(k["nb"], k["link"]) for k in kayit}
    satirlar.append(f"[0] Mevcut yontem (baslik + link): {n - len(tam)} mükerrer elendi, "
                   f"{len(tam)} benzersiz")

    # 1) Sadece normalize baslik
    b1 = {k["nb"] for k in kayit}
    satirlar.append(f"[1] Sadece normalize baslik: {n - len(b1)} mükerrer ({n - len(b1)}/{n} = "
                   f"{(n - len(b1)) * 100 / n:.1f}%)")

    # 2) Ortak kelime esikleri (zaman penceresi icinde)
    for esik in (3, 4, 5):
        for pencere_saat in (6, 12):
            pencere = timedelta(hours=pencere_saat)
            ciftler = set()
            for i, j in combinations(range(n), 2):
                a, b = kayit[i], kayit[j]
                if a["kaynak"] == b["kaynak"]:
                    continue
                if abs(a["tarih"] - b["tarih"]) > pencere:
                    continue
                ortak = a["kb"] & b["kb"]
                if len(ortak) >= esik:
                    ciftler.add((i, j))
            satirlar.append(f"[2] Ortak kelime >= {esik}, {pencere_saat} saat, farkli kaynak: "
                           f"{len(ciftler)} cift")

    # 3) Baslik Jaccard benzerligi
    for esik in (0.6, 0.7, 0.8):
        ciftler = set()
        for i, j in combinations(range(n), 2):
            a, b = kayit[i], kayit[j]
            if a["kaynak"] == b["kaynak"]:
                continue
            if abs(a["tarih"] - b["tarih"]) > timedelta(hours=12):
                continue
            if jaccard(a["kb"], b["kb"]) >= esik:
                ciftler.add((i, j))
        satirlar.append(f"[3] Baslik Jaccard >= {esik}, 12 saat, farkli kaynak: "
                       f"{len(ciftler)} cift")

    # 4) Aciklama benzerligi
    for esik in (0.5, 0.6):
        ciftler = set()
        for i, j in combinations(range(n), 2):
            a, b = kayit[i], kayit[j]
            if a["kaynak"] == b["kaynak"]:
                continue
            if abs(a["tarih"] - b["tarih"]) > timedelta(hours=12):
                continue
            if jaccard(a["ka"], b["ka"]) >= esik:
                ciftler.add((i, j))
        satirlar.append(f"[4] Aciklama Jaccard >= {esik}, 12 saat, farkli kaynak: "
                       f"{len(ciftler)} cift")

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "sonuc":
        with open("tests/mukerrer-sonuc.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(elenenleri_goster("tests/tmp-h.json")) + "\n")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "ornek":
        with open("tests/mukerrer-ornek.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(ornekler(kayit, 0.7, 0.6)) + "\n")
        return

    with open("tests/mukerrer-raporu.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


if __name__ == "__main__":
    main()