import java.util.Properties

// UYGULAMA MODÜLÜ — WebView tabanlı HABER TV (Xiaomi TV Box hedefli)
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.habertv.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.habertv.app"
        // minSdk 26: adaptive ikon + Android TV özellikleri için gerekli.
// (Xiaomi TV Box cihazları Android 9 / API 28+ çalışır.)
minSdk = 26
        targetSdk = 35
        versionCode = 2
        versionName = "1.1"
    }

    signingConfigs {
        create("release") {
            val ks = rootProject.file("keystore.properties")
            if (ks.exists()) {
                val p = Properties().apply { ks.inputStream().use { load(it) } }
                storeFile = file(p.getProperty("storeFile"))
                storePassword = p.getProperty("storePassword")
                keyAlias = p.getProperty("keyAlias")
                keyPassword = p.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        debug { isMinifyEnabled = false }
        release {
            isMinifyEnabled = false
            // keystore yoksa debug imzasıyla imzalanır (kurulum kolaylığı).
            signingConfig = if (rootProject.file("keystore.properties").exists()) {
                signingConfigs.getByName("release")
            } else {
                signingConfigs.getByName("debug")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    androidResources {
        // Web dosyaları sıkıştırılmasın; WebView fetch ile doğrudan okuyor
        noCompress += listOf("json", "html", "js", "css", "xml")
    }
}

// ── Web varlıklarını APK'ya göm ──────────────────────────────
// bot.py haberler.json'u düzenli üretir; bu görev her build'de web dosyalarını
// yeniden kopyalar, böylece APK daima o anki güncel veriyi taşır.
val webKlasor = rootProject.file("..")

val webVarliklari = tasks.register<Copy>("webVarliklariKopyala") {
    description = "index.html, assets/, feeds/ ve JSON dosyalarını APK'ya gömer"
    from(webKlasor) {
        include("index.html")
        include("haberler.json")
        include("bot-raporu.json")
        include("config.json")
    }
    from(webKlasor.resolve("assets")) { into("assets") }
    from(webKlasor.resolve("feeds")) { into("feeds") }
    into(layout.buildDirectory.dir("generated/webVarliklari"))
}

android.sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/webVarliklari"))

tasks.named("preBuild") { dependsOn(webVarliklari) }

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.webkit:webkit:1.12.1")
    implementation("androidx.core:core-ktx:1.13.1")
}