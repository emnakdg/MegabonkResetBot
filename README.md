# Megabonk Auto R Bot

Megabonk oyununda istediğin düşman sayısına sahip haritayı otomatik olarak bulan bot.  
Ekranı okur, şartlar sağlanana kadar **R** tuşuna basar; hedef harita gelince **ESC** ile kabul eder.

---

## Kurulum (İlk Kez Kullanıyorsan)

### 1. Tesseract-OCR Kur
Bot, ekrandaki yazıları okuyabilmek için **Tesseract-OCR** adlı ücretsiz bir programa ihtiyaç duyar.

**Otomatik kurulum için:**  
`Tesseract_Kur.bat` dosyasına **çift tıkla** ve bitimini bekle.

> ⚠️ Kurulum sırasında internet bağlantısı gereklidir.  
> Kurulum tamamlandıktan sonra botu açabilirsin.

---

### 2. Botu Çalıştır

**`.exe` ile (tavsiye edilen):**  
`megabonk_bot.exe` dosyasına çift tıkla.

**Python ile (geliştiriciler için):**  
`baslat.bat` dosyasına çift tıkla. Gerekli kütüphaneler otomatik kurulur ve bot başlar.

---

## Kullanım

| Alan | Açıklama |
|------|----------|
| **Minimum Moais Sayısı** | Haritada en az kaç Moais olsun |
| **Minimum Shady Guy Sayısı** | Haritada en az kaç Shady Guy olsun |
| **Minimum Microwaves Sayısı** | Haritada en az kaç Microwave olsun |
| **ESC Gecikmesi** | Hedef bulununca ESC'ye basmadan önce kaç saniye beklensin |

1. Megabonk'u aç ve harita seçim ekranına gel.
2. Ayarlarını gir.
3. **Başlat (F8)** butonuna bas veya `F8` tuşuna bas.
4. Bot istediğin haritayı bulunca sesi duyarsın ve otomatik durur.
5. İstediğin zaman **Durdur (F9)** veya `F9` ile durdurabilirsin.

---

## Güncelleme

Bot açıldığında otomatik olarak güncelleme kontrolü yapar.  
Yeni sürüm varsa bir pencere açılır — **"Güncelle"** butonuna tıklaman yeterli, geri kalanı otomatik yapılır.

---

## Sorun Giderme

**"Tesseract bulunamadı" hatası alıyorum:**  
→ `Tesseract_Kur.bat` dosyasını çalıştır ve kurulumun tamamlandığından emin ol.

**Bot ekrandan yanlış sayılar okuyor:**  
→ Arayüzdeki **OCR Debug Modu** kutucuğunu işaretle. Botun ekrandan ne gördüğünü ayrı pencerede görebilirsin.

**Bot hiç çalışmıyor / tepki vermiyor:**  
→ Oyunun harita seçim ekranında olduğundan emin ol.
