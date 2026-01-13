# Requirements Document

## Introduction

TezgahTakip uygulamasında v2.0.0'dan v2.1.3'e güncelleme sırasında yaşanan "base_library.zip" bulunamama hatası ve frozen_importlib_bootstrap sorunlarının çözülmesi için gerekli düzeltmelerin yapılması.

## Glossary

- **Update_System**: Otomatik güncelleme sistemi
- **Launcher**: Uygulama başlatıcısı
- **Base_Library**: PyInstaller tarafından oluşturulan temel kütüphane dosyası
- **Frozen_Importlib**: Python'un donmuş import sistemi
- **Executable**: Çalıştırılabilir uygulama dosyası

## Requirements

### Requirement 1: Güncelleme Uyumluluğu

**User Story:** Kullanıcı olarak, v2.0.0'dan v2.1.3'e güncelleme yaptığımda uygulama sorunsuz çalışmasını istiyorum.

#### Acceptance Criteria

1. WHEN kullanıcı otomatik güncelleme yapar THEN Update_System SHALL eski dosyaları temizler ve yeni dosyaları doğru konuma yerleştirir
2. WHEN güncelleme tamamlanır THEN Launcher SHALL base_library.zip dosyasını doğru konumda bulabilir
3. WHEN uygulama yeniden başlatılır THEN Frozen_Importlib SHALL tüm modülleri başarıyla yükler
4. IF güncelleme sırasında hata oluşur THEN Update_System SHALL kullanıcıya açık hata mesajı gösterir ve rollback seçeneği sunar

### Requirement 2: Dosya Yolu Çözümleme

**User Story:** Sistem yöneticisi olarak, uygulamanın farklı kurulum konumlarında çalışabilmesini istiyorum.

#### Acceptance Criteria

1. WHEN uygulama başlatılır THEN Launcher SHALL mevcut çalışma dizinini doğru tespit eder
2. WHEN base_library.zip aranır THEN Update_System SHALL birden fazla olası konumu kontrol eder
3. WHEN dosya bulunamaz THEN Update_System SHALL alternatif yolları dener
4. WHEN tüm yollar başarısız olur THEN Update_System SHALL kullanıcıya manuel çözüm önerir

### Requirement 3: Güncelleme Güvenliği

**User Story:** Kullanıcı olarak, güncelleme sırasında verilerimin korunmasını ve eski sürüme dönebilmeyi istiyorum.

#### Acceptance Criteria

1. WHEN güncelleme başlar THEN Update_System SHALL mevcut sürümün yedeğini oluşturur
2. WHEN güncelleme başarısız olur THEN Update_System SHALL otomatik olarak eski sürüme geri döner
3. WHEN rollback yapılır THEN Update_System SHALL kullanıcı verilerini korur
4. WHEN güncelleme tamamlanır THEN Update_System SHALL eski yedek dosyalarını temizler

### Requirement 4: Hata Raporlama

**User Story:** Geliştirici olarak, güncelleme hatalarının detaylı loglarını görebilmek istiyorum.

#### Acceptance Criteria

1. WHEN güncelleme hatası oluşur THEN Update_System SHALL detaylı hata logunu kaydeder
2. WHEN hata raporu oluşturulur THEN Update_System SHALL sistem bilgilerini dahil eder
3. WHEN kullanıcı hata raporu gönderir THEN Update_System SHALL log dosyasını otomatik ekler
4. WHEN hata çözülür THEN Update_System SHALL başarı durumunu loglar

### Requirement 5: Manuel Güncelleme Desteği

**User Story:** Kullanıcı olarak, otomatik güncelleme başarısız olduğunda manuel güncelleme yapabilmek istiyorum.

#### Acceptance Criteria

1. WHEN otomatik güncelleme başarısız olur THEN Update_System SHALL manuel güncelleme seçeneği sunar
2. WHEN manuel güncelleme seçilir THEN Update_System SHALL adım adım talimatlar gösterir
3. WHEN manuel dosya kopyalama yapılır THEN Update_System SHALL dosya bütünlüğünü kontrol eder
4. WHEN manuel güncelleme tamamlanır THEN Update_System SHALL yeni sürümü doğrular