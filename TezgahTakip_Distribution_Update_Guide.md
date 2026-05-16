# Tezgah Takip Uygulaması: Dağıtım ve Otomatik Güncelleme Rehberi

Bu rehber, Tezgah Takip uygulamasının son kullanıcılar için nasıl dağıtılacağını, kurulacağını ve otomatik olarak nasıl güncelleneceğini açıklamaktadır. Amacımız, uygulamanızı Python bağımlılıklarıyla uğraşmadan, tek bir kurulum dosyasıyla kolayca erişilebilir hale getirmektir.

## 1. Neden Bu Yaklaşım?

Uygulamanızı bir Windows kurulum dosyası (Setup.exe) olarak dağıtmak ve otomatik güncelleme mekanizması eklemek, kullanıcı deneyimini önemli ölçüde artırır:

*   **Kolay Kurulum**: Kullanıcılar, Python veya diğer teknik detaylarla uğraşmadan, standart bir Windows programı gibi uygulamayı kurabilirler.
*   **Tek Tıkla Güncelleme**: Uygulama her açıldığında otomatik olarak güncellemeleri kontrol eder ve yeni bir sürüm olduğunda kullanıcıya bildirir. Kullanıcılar tek bir tıklamayla uygulamalarını güncelleyebilirler.
*   **Profesyonel Görünüm**: Uygulamanız, profesyonel bir masaüstü yazılımı gibi görünür ve hissedilir.
*   **Bağımlılık Yönetimi**: Tüm gerekli kütüphaneler ve bağımlılıklar kurulum dosyasına dahil edildiği için, kullanıcıların ek bir yazılım yüklemesine gerek kalmaz.

## 2. Kurulum Süreci (Son Kullanıcı İçin)

Tezgah Takip uygulamasını kurmak oldukça basittir:

1.  **Kurulum Dosyasını İndirin**: Size sağlanacak olan `TezgahTakip_Setup_vX.X.X.exe` (buradaki X.X.X sürüm numarasını temsil eder) adlı kurulum dosyasını indirin.
2.  **Kurulumu Başlatın**: İndirdiğiniz `.exe` dosyasına çift tıklayın.
3.  **Kurulum Sihirbazını Takip Edin**: Karşınıza çıkan kurulum sihirbazındaki adımları takip edin. Genellikle "İleri", "Kabul Ediyorum" ve "Kur" düğmelerine tıklamanız yeterli olacaktır.
4.  **Kısayolları Oluşturun**: Kurulum sırasında masaüstüne veya Başlat Menüsü'ne kısayol oluşturma seçeneğini işaretleyebilirsiniz.
5.  **Uygulamayı Başlatın**: Kurulum tamamlandıktan sonra, masaüstündeki veya Başlat Menüsü'ndeki Tezgah Takip kısayoluna tıklayarak uygulamayı başlatabilirsiniz.

## 3. Otomatik Güncelleme Nasıl Çalışır?

Uygulamanızın her zaman güncel kalmasını sağlamak için entegre bir otomatik güncelleme sistemi bulunmaktadır:

1.  **Başlangıçta Kontrol**: Uygulama her başlatıldığında, internet üzerinden GitHub Releases sayfasındaki en son sürümü kontrol eder.
2.  **Güncelleme Bildirimi**: Eğer mevcut sürümünüzden daha yeni bir sürüm varsa, uygulama size bir bildirim gösterir ve yeni özellikler veya hata düzeltmeleri hakkında bilgi verir.
3.  **Onay ve İndirme**: Güncellemeyi yüklemek isteyip istemediğiniz sorulur. Onay verdiğinizde, yeni sürüm otomatik olarak indirilir.
4.  **Kurulum ve Yeniden Başlatma**: İndirme tamamlandıktan sonra, uygulama kendini günceller ve değişikliklerin etkili olması için yeniden başlatılmasını ister. Onay verdiğinizde uygulama otomatik olarak kapanır ve güncel haliyle tekrar açılır.
5.  **Geri Dönüş (Rollback)**: Nadiren de olsa bir güncelleme sırasında sorun yaşanırsa, uygulama otomatik olarak bir önceki çalışan sürüme geri dönebilir, böylece veri kaybı veya kesinti yaşanmaz.

## 4. Teknik Detaylar (Geliştiriciler İçin)

Bu sistemin arkasında aşağıdaki teknolojiler ve süreçler bulunmaktadır:

*   **Paketleme**: Python kodları ve bağımlılıkları, **PyInstaller** kullanılarak tek veya birkaç `.exe` dosyasına dönüştürülür.
*   **Güncelleme Mekanizması**: Uygulama içinde özel olarak geliştirilmiş bir `auto_updater.py` modülü, GitHub API'sini kullanarak yeni sürümleri kontrol eder ve indirir. Güncellemeler genellikle sıkıştırılmış ZIP dosyaları olarak yayınlanır.
*   **Kurulum Dosyası**: **Inno Setup** kullanılarak, PyInstaller tarafından oluşturulan `.exe` dosyaları ve diğer gerekli varlıklar (ikonlar, yapılandırma dosyaları) profesyonel bir `.exe` kurulum dosyasına dönüştürülür. Bu kurulum dosyası, masaüstü kısayolları oluşturma, program ekle/kaldır desteği gibi standart Windows kurulum özelliklerini sağlar.
*   **Build Script**: Tüm bu adımlar, bir Python betiği (`build_executable.py` veya benzeri) aracılığıyla otomatikleştirilir. Bu betik, tek bir komutla uygulamanın yeni bir sürümünü paketleyebilir, kurulum dosyasını oluşturabilir ve hatta GitHub Releases'a yüklemeye hazır hale getirebilir.

## 5. Sonraki Adımlar

Bu rehberde açıklanan stratejiyi uygulamak için:

1.  Uygulamanızın ana Python kodlarını (özellikle `tezgah_takip_app.py` ve `launcher.py` gibi ana giriş noktalarını) PyInstaller ile uyumlu hale getirin.
2.  `auto_updater.py` modülünü GitHub Releases ile entegre edin ve test edin.
3.  `build_executable.py` betiğini uygulamanızın yapısına göre özelleştirin.
4.  `TezgahTakip_Setup_Script.iss` dosyasını (Inno Setup scripti) uygulamanızın dosyalarını ve gereksinimlerini yansıtacak şekilde güncelleyin.

Bu adımlar tamamlandığında, kullanıcılarınıza dağıtımı kolay, otomatik güncellenen ve profesyonel bir Windows masaüstü uygulaması sunabileceksiniz.
