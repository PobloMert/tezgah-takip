# Tezgah Takip: Windows Dağıtım ve Otomatik Güncelleme Stratejisi

Bu rapor, Tezgah Takip uygulamasının Python tabanlı bir scriptten, son kullanıcılar için dağıtımı kolay, profesyonel bir Windows masaüstü uygulamasına dönüştürülmesi için gereken adımları ve stratejiyi detaylandırmaktadır.

## 1. Uygulama Paketleme (EXE Oluşturma)

Uygulamanın Python yüklü olmayan bilgisayarlarda da çalışabilmesi için **PyInstaller** kullanılacaktır.

*   **Yöntem**: `onefile` (tek bir EXE) veya `onedir` (tüm bağımlılıkların bir klasörde toplandığı yapı).
*   **Launcher Yapısı**: Uygulama, ana uygulama dosyası (`TezgahTakip.exe`) ve bir başlatıcı (`TezgahTakip_Launcher.exe`) olmak üzere iki parçalı bir yapıda paketlenecektir. Başlatıcı, uygulama açılmadan önce güncellemeleri kontrol edecek ve gerekirse güncelleyecektir.
*   **Varlık Yönetimi**: Simge dosyaları (`.ico`), resimler (`.png`, `.svg`) ve yapılandırma dosyaları (`config.json`, `settings.json`) EXE içerisine gömülecek veya EXE'nin yanına düzgün bir şekilde yerleştirilecektir.

## 2. Otomatik Güncelleme Sistemi

Uygulamanın her zaman güncel kalmasını sağlamak için **GitHub Releases** tabanlı bir mekanizma kullanılacaktır.

*   **Mekanizma**: `auto_updater.py` modülü, GitHub API'sini kullanarak en son yayınlanan sürümü kontrol eder.
*   **İş Akışı**:
    1.  Uygulama başlatıldığında `AutoUpdater` çalışır.
    2.  Mevcut sürüm ile GitHub'daki en son sürüm karşılaştırılır.
    3.  Yeni sürüm varsa, kullanıcıya bir bildirim gösterilir.
    4.  Onay alınırsa, yeni sürüm (ZIP formatında) indirilir, mevcut dosyalar yedeklenir ve yeni dosyalar üzerine yazılır.
    5.  Uygulama yeniden başlatılır.
*   **Geri Dönüş (Rollback)**: Güncelleme sırasında bir hata oluşursa, sistem otomatik olarak yedeklenen bir önceki sürüme geri döner.

## 3. Kurulum (Setup) Dosyası Oluşturma

Son kullanıcıların uygulamayı kolayca kurabilmesi için **Inno Setup** kullanılacaktır.

*   **Özellikler**:
    *   Masaüstü ve Başlat Menüsü kısayolları oluşturma.
    *   Gerekli çalışma zamanı bileşenlerinin kontrolü.
    *   Kullanıcı dostu kurulum arayüzü (Dil desteği ile).
    *   Uygulama dosyalarının güvenli bir şekilde `C:\Program Files` veya `AppData` altına yerleştirilmesi.
    *   Program ekle/kaldır desteği.

## 4. Dağıtım Süreci Otomasyonu

Geliştiricinin (sizin) tek bir komutla yeni sürümü hazırlayıp dağıtabilmesi için bir **Build System** kurulacaktır.

*   **Build Script (`build_system.py`)**:
    1.  Kodları temizler ve hazırlar.
    2.  PyInstaller ile EXE dosyalarını oluşturur.
    3.  Gerekli tüm dosyaları (EXE, ikonlar, config) bir araya getirir.
    4.  Inno Setup scriptini çalıştırarak `.exe` uzantılı kurulum dosyasını (Setup) üretir.
    5.  Opsiyonel olarak, "Portable" (kurulum gerektirmeyen) bir ZIP paketi oluşturur.

## 5. Önerilen Yol Haritası

| Adım | İşlem | Araç |
| :--- | :--- | :--- |
| **1** | Mevcut kodların Windows uyumluluğunun kontrolü | Python 3.11+ |
| **2** | EXE paketleme betiğinin hazırlanması | PyInstaller |
| **3** | GitHub API entegrasyonlu güncelleme modülü | `requests`, `github-api` |
| **4** | Inno Setup scriptinin yazılması | Inno Setup Compiler |
| **5** | Tüm süreci otomatikleştiren Build Script | Python |

## Sonuç

Bu strateji uygulandığında, kullanıcılarınız Python ile uğraşmak zorunda kalmayacak, sadece bir `Setup.exe` dosyasını çalıştırarak uygulamayı kuracak ve her açılışta güncellemeleri otomatik olarak alacaklardır. Bu, uygulamanızın profesyonelliğini ve kullanıcı deneyimini en üst seviyeye taşıyacaktır.
