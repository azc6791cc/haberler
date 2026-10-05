"""Denetim: test_data ve feeds dosyaları sources.json ile tutarlı mı?
Çıktı: tests/denetim.txt
"""
import json
import os
import re

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dosya_adlari_uret(url):
    """bot.py besleme_cek() ve fetch_fixtures.py ile BİREBİR aynı adlandırma."""
    return re.sub(r"[^a-z0-9]+", "_", url.lower()).strip("_")[:80] + ".xml"


def main():
    with open(os.path.join(KOK, "sources.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    kayit = set()
    for k in cfg["kaynaklar"]:
        for b in k["beslemeler"]:
            kayit.add(dosya_adlari_uret(b["url"]))

    td = os.path.join(KOK, "tests", "test_data")
    # ornek_*.xml dosyaları elle yazılmış SABİT test verisidir; beslemeye bağlı değildir.
    sabit = {a for a in os.listdir(td) if a.startswith("ornek_")} if os.path.isdir(td) else set()
    mevcut = set(os.listdir(td)) - sabit if os.path.isdir(td) else set()

    satirlar = []
    satirlar.append(f"sources.json besleme sayisi : {len(kayit)}")
    satirlar.append(f"tests/test_data dosya sayisi: {len(mevcut)} besleme + {len(sabit)} sabit")

    eksik = sorted(kayit - set(mevcut))
    artik = sorted(set(mevcut) - kayit)
    satirlar.append("")
    satirlar.append(f"KAYITSIZ (test verisi olmayan, {len(eksik)}):")
    for e in eksik:
        satirlar.append("  - " + e)
    satirlar.append("")
    satirlar.append(f"ARTIK (sources.json'da olmayan, {len(artik)}):")
    for a in artik:
        satirlar.append("  - " + a)

    # feeds klasörü
    feeds = os.path.join(KOK, "feeds")
    fd = sorted(os.listdir(feeds)) if os.path.isdir(feeds) else []
    beklenen = {"tum.xml"}
    def slug(a):
        t = a.lower()
        for k_, v in [("ş", "s"), ("ğ", "g"), ("ü", "u"), ("ı", "i"),
                      ("ö", "o"), ("ç", "c"), ("â", "a"), ("î", "i")]:
            t = t.replace(k_, v)
        return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "tum"
    for kat in cfg["kategoriler"]:
        beklenen.add(slug(kat) + ".xml")
    satirlar.append("")
    satirlar.append(f"feeds/ dosya sayisi: {len(fd)}  (beklenen {len(beklenen)})")
    satirlar.append(f"  eksik : {sorted(beklenen - set(fd))}")
    satirlar.append(f"  artik : {sorted(set(fd) - beklenen)}")

    with open(os.path.join(KOK, "tests", "denetim.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


if __name__ == "__main__":
    main()