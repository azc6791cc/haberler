# HABER TV — Android TV / Xiaomi TV Box APK Projesi

Bu klasör, bir klasör üstündeki (`..`) web uygulamasını **Android TV** için APK'ya
çeviren bir WebView sarmalayıcıdır. Uygulama **tamamen çevrimdışıdır** — hiçbir
sunucuya bağlanmaz, hiçbir veri göndermez.

## Gereksinimler
- Android Studio (Ladybug 2024.2.2 veya üzeri)
- JDK 17 (Android Studio ile birlikte gelir)
- Android SDK 35

## Derleme

### Android Studio ile (kolay yol)
1. **File → Open** → `android/` klasörünü seç
2. Gradle sync'in bitmesini bekle (SDK 35 kurulumu istenirse kabul et)
3. **Build → Build Bundle(s) / APK(s) → Build APK(s)**
4. Çıktı: `android/app/build/outputs/apk/debug/app-debug.apk`

### Komut satırından
```bash
cd android
gradlew.bat assembleDebug     # test APK'sı
gradlew.bat assembleRelease   # dağıtım APK'sı
```

## Haberler APK'ya nasıl giriyor? (çevrimiçi + gömülü yedek)

APK **bir kez derlenir**; her açılışta internetten güncellenir:

1. **Uzak kaynak (öncelik):** `config.json` → `uzak_taban_url` (örn.
   `https://kullanici.github.io/haberler/`). `app.js` açılışta önce
   `<URL>/haberler.json` + `<URL>/bot-raporu.json` dosyalarını çeker (12 sn zaman aşımı).
2. **Gömülü yedek:** İnternet yoksa / URL boşsa / sunucu cevap vermezse
   APK içindeki `haberler.json` gösterilir. Bu yüzden derlemeden önce bir kez
   `bot.py` çalıştır ki yedek de dolu olsun.
3. **Kullanıcı girdisi:** Ayarlar → Çevrimiçi Güncelleme → Haber kaynağı
   kutusuna URL yazılabilir; bu, `config.json` değerini ezer
   (`localStorage`'da saklanır). Kaynak rozeti (`canlı`/`gömülü`) bot kartında görünür.

`app/build.gradle.kts` içindeki `webVarliklariKopyala` görevi her derlemede
şu dosyaları APK'ya gömer (yedek + arayüz için):

```
index.html, config.json, assets/css/style.css, assets/js/app.js,
haberler.json, bot-raporu.json, feeds/*.xml
```

### Uzak adresi yayına alma (örnek: GitHub Pages)

```bash
python bot.py                        # haberler.json üret
# haberler.json + bot-raporu.json + config.json'u
# GitHub repo'na koy, Settings → Pages → Deploy from branch
# URL'yi config.json'a yaz: {"uzak_taban_url": "https://kullanici.github.io/haberler/"}
```

Önemli: adres **HTTPS** olmalı ve `haberler.json`'u CORS'a açık sunmalı
(GitHub Pages varsayılan olarak açıktır).

## Release imzalama (keystore)

Keystore olmadan da release APK üretilir (debug imzasıyla, kurulabilir).
Kalıcı ve Play Store'a uygun imza için:

```bash
keytool -genkeypair -v -keystore habertv.jks -keyalg RSA -keysize 2048 \
  -validity 10000 -alias habertv
```

Ardından `android/keystore.properties` dosyası oluştur:
```properties
storeFile=habertv.jks
storePassword=******
keyAlias=habertv
keyPassword=******
```
Bu dosya `.gitignore`'da ve ASLA paylaşılmamalı.

## TV'de kurulum

1. APK'yı USB/SD kart ile TV Box'a kopyalayın
2. TV Box → Ayarlar → Güvenlik → Bilinmeyen kaynaklardan yükleme: **AÇ**
3. Dosya yöneticisiyle APK'ya tıklayın ve kurun
4. Ana ekranda **HABER TV** simgesi görünecek

## Kumandayla kullanım

| Tuş | İşlev |
|---|---|
| Yön tuşları (◀ ▶ ▲ ▼) | Kategori ve haber kartları arasında gezinme |
| OK / Enter | Seçili haberi aç |
| Geri | Ana ekrana dön |
| Kategori çubuğunda ◀ ▶ | Uzun listede kaydırma |

## Mimari notlar

- **CORS çözümü:** Web varlıkları `file://` ile değil,
  `https://appassets.androidplatform.net/assets/` üzerinden sunulur
  (`WebViewAssetLoader`). Aksi halde `fetch('haberler.json')` CORS hatası verir
  ve uygulama veriyi yükleyemezdi.
- **TV modu:** `MainActivity` UserAgent'a `HABERTV/1.0` damgası ekler; `app.js`
  bunu görünce kumanda gezinimini ve büyük puntoyu devreye alır.
- **Harici linkler** (haber kaynakları) uygulamada değil, sistem tarayıcısında açılır.