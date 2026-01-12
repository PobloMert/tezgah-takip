#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip Logo Oluşturucu
Uygulama için uygun logo tasarımı
"""

def create_tezgah_logo_svg():
    """TezgahTakip logosunu SVG formatında oluştur"""
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2E7D32;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="machineGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFF;stop-opacity:0.9" />
      <stop offset="100%" style="stop-color:#E0E0E0;stop-opacity:0.8" />
    </linearGradient>
  </defs>
  
  <!-- Arka plan daire -->
  <circle cx="64" cy="64" r="60" fill="url(#bgGradient)" stroke="#1B5E20" stroke-width="2"/>
  
  <!-- Tezgah makinesi ana gövde -->
  <rect x="25" y="45" width="78" height="45" rx="4" fill="url(#machineGradient)" stroke="#666" stroke-width="1"/>
  
  <!-- Makine kontrol paneli -->
  <rect x="30" y="50" width="25" height="15" rx="2" fill="#333" stroke="#555" stroke-width="1"/>
  
  <!-- Kontrol butonları -->
  <circle cx="35" cy="57" r="2" fill="#FF5722"/>
  <circle cx="42" cy="57" r="2" fill="#4CAF50"/>
  <circle cx="49" cy="57" r="2" fill="#2196F3"/>
  
  <!-- Makine çalışma alanı -->
  <rect x="60" y="50" width="35" height="25" rx="2" fill="#E3F2FD" stroke="#1976D2" stroke-width="1"/>
  
  <!-- Çalışma parçası -->
  <rect x="65" y="55" width="25" height="15" rx="1" fill="#FFC107" stroke="#F57F17" stroke-width="1"/>
  
  <!-- Makine ayakları -->
  <rect x="30" y="85" width="8" height="12" fill="#666"/>
  <rect x="90" y="85" width="8" height="12" fill="#666"/>
  
  <!-- AI sembolü (beyin ikonu) -->
  <g transform="translate(75, 25)">
    <circle cx="12" cy="12" r="10" fill="#FF9800" stroke="#E65100" stroke-width="1"/>
    <path d="M 6 8 Q 12 4 18 8 Q 18 12 12 16 Q 6 12 6 8" fill="#FFF" opacity="0.8"/>
    <circle cx="9" cy="9" r="1" fill="#E65100"/>
    <circle cx="15" cy="9" r="1" fill="#E65100"/>
  </g>
  
  <!-- Takip çizgileri (monitoring) -->
  <g stroke="#4CAF50" stroke-width="2" fill="none" opacity="0.7">
    <path d="M 15 25 Q 25 20 35 25"/>
    <path d="M 15 30 Q 25 25 35 30"/>
    <path d="M 15 35 Q 25 30 35 35"/>
  </g>
  
  <!-- Veri akışı noktaları -->
  <circle cx="15" cy="25" r="1.5" fill="#4CAF50"/>
  <circle cx="25" cy="22" r="1" fill="#4CAF50"/>
  <circle cx="35" cy="25" r="1.5" fill="#4CAF50"/>
  
  <!-- Başlık metni -->
  <text x="64" y="115" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1B5E20">TezgahTakip</text>
</svg>'''
    return svg_content

def create_tezgah_logo_png():
    """TezgahTakip logosunu PNG formatında oluştur"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # 128x128 boyutunda resim oluştur
        size = (128, 128)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Arka plan daire (gradient yerine solid renk)
        center = (64, 64)
        radius = 60
        draw.ellipse([center[0]-radius, center[1]-radius, 
                     center[0]+radius, center[1]+radius], 
                    fill=(76, 175, 80, 255), outline=(27, 94, 32, 255), width=2)
        
        # Tezgah makinesi ana gövde
        draw.rounded_rectangle([25, 45, 103, 90], radius=4, 
                             fill=(240, 240, 240, 230), outline=(102, 102, 102, 255), width=1)
        
        # Kontrol paneli
        draw.rounded_rectangle([30, 50, 55, 65], radius=2, 
                             fill=(51, 51, 51, 255), outline=(85, 85, 85, 255), width=1)
        
        # Kontrol butonları
        draw.ellipse([33, 55, 37, 59], fill=(255, 87, 34, 255))  # Kırmızı
        draw.ellipse([40, 55, 44, 59], fill=(76, 175, 80, 255))  # Yeşil
        draw.ellipse([47, 55, 51, 59], fill=(33, 150, 243, 255)) # Mavi
        
        # Çalışma alanı
        draw.rounded_rectangle([60, 50, 95, 75], radius=2, 
                             fill=(227, 242, 253, 255), outline=(25, 118, 210, 255), width=1)
        
        # Çalışma parçası
        draw.rounded_rectangle([65, 55, 90, 70], radius=1, 
                             fill=(255, 193, 7, 255), outline=(245, 127, 23, 255), width=1)
        
        # Makine ayakları
        draw.rectangle([30, 85, 38, 97], fill=(102, 102, 102, 255))
        draw.rectangle([90, 85, 98, 97], fill=(102, 102, 102, 255))
        
        # AI sembolü (basit daire)
        ai_center = (87, 37)
        draw.ellipse([ai_center[0]-10, ai_center[1]-10, 
                     ai_center[0]+10, ai_center[1]+10], 
                    fill=(255, 152, 0, 255), outline=(230, 81, 0, 255), width=1)
        
        # AI içi
        draw.ellipse([ai_center[0]-6, ai_center[1]-6, 
                     ai_center[0]+6, ai_center[1]+6], 
                    fill=(255, 255, 255, 200))
        
        # AI gözler
        draw.ellipse([ai_center[0]-4, ai_center[1]-2, ai_center[0]-2, ai_center[1]], fill=(230, 81, 0, 255))
        draw.ellipse([ai_center[0]+2, ai_center[1]-2, ai_center[0]+4, ai_center[1]], fill=(230, 81, 0, 255))
        
        # Takip çizgileri (basit çizgiler)
        draw.line([(15, 25), (35, 25)], fill=(76, 175, 80, 180), width=2)
        draw.line([(15, 30), (35, 30)], fill=(76, 175, 80, 180), width=2)
        draw.line([(15, 35), (35, 35)], fill=(76, 175, 80, 180), width=2)
        
        # Veri noktaları
        draw.ellipse([13, 23, 17, 27], fill=(76, 175, 80, 255))
        draw.ellipse([24, 21, 26, 23], fill=(76, 175, 80, 255))
        draw.ellipse([33, 23, 37, 27], fill=(76, 175, 80, 255))
        
        # Metin ekleme (basit font)
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        text = "TezgahTakip"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (128 - text_width) // 2
        draw.text((text_x, 110), text, fill=(27, 94, 32, 255), font=font)
        
        return img
        
    except ImportError:
        print("PIL (Pillow) kütüphanesi bulunamadı. SVG versiyonu kullanılacak.")
        return None
    except Exception as e:
        print(f"PNG logo oluşturma hatası: {e}")
        return None

def create_simple_icon():
    """Basit ikon oluştur (PIL olmadan)"""
    try:
        from PIL import Image, ImageDraw
        
        # 32x32 basit ikon
        size = (32, 32)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Arka plan
        draw.ellipse([2, 2, 30, 30], fill=(76, 175, 80, 255), outline=(27, 94, 32, 255), width=1)
        
        # Basit makine
        draw.rectangle([8, 12, 24, 20], fill=(240, 240, 240, 255), outline=(102, 102, 102, 255), width=1)
        
        # Kontrol noktası
        draw.ellipse([10, 14, 12, 16], fill=(255, 87, 34, 255))
        draw.ellipse([14, 14, 16, 16], fill=(76, 175, 80, 255))
        
        return img
        
    except ImportError:
        return None

if __name__ == "__main__":
    print("🏭 TezgahTakip logosu oluşturuluyor...")
    
    # PNG logo oluştur
    logo = create_tezgah_logo_png()
    if logo:
        logo.save("tezgah_logo.png")
        print("✅ TezgahTakip logosu tezgah_logo.png olarak kaydedildi")
        
        # Küçük ikon da oluştur
        try:
            from PIL import Image
            icon = logo.resize((32, 32), Image.Resampling.LANCZOS)
            icon.save("tezgah_icon.ico", format='ICO')
            print("✅ TezgahTakip ikonu tezgah_icon.ico olarak kaydedildi")
        except:
            print("⚠️ İkon oluşturulamadı")
    else:
        print("⚠️ PNG logo oluşturulamadı, SVG versiyonu oluşturuluyor...")
    
    # SVG logo oluştur
    svg_content = create_tezgah_logo_svg()
    with open("tezgah_logo.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("✅ TezgahTakip logosu tezgah_logo.svg olarak kaydedildi")
    
    print("\n🎨 Logo dosyaları hazır:")
    print("   • tezgah_logo.png (128x128 ana logo)")
    print("   • tezgah_icon.ico (32x32 ikon)")
    print("   • tezgah_logo.svg (vektör logo)")