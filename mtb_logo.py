#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTB Logo - SVG formatında logo oluşturma
"""

def create_mtb_logo_svg():
    """MTB logosunu SVG formatında oluştur"""
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="200" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
  <!-- MTB Logo -->
  <g fill="#E53E3E">
    <!-- M harfi -->
    <polygon points="20,50 20,150 40,150 40,80 60,120 80,80 80,150 100,150 100,50 80,50 60,90 40,50"/>
    
    <!-- T harfi -->
    <rect x="120" y="50" width="80" height="20"/>
    <rect x="150" y="50" width="20" height="100"/>
    
    <!-- B harfi -->
    <path d="M220,50 L220,150 L280,150 Q300,150 300,130 Q300,110 285,100 Q300,90 300,70 Q300,50 280,50 Z
             M240,70 L240,90 L275,90 Q280,90 280,80 Q280,70 275,70 Z
             M240,110 L240,130 L275,130 Q285,130 285,120 Q285,110 275,110 Z"/>
  </g>
  
  <!-- Alt çizgi -->
  <rect x="20" y="160" width="280" height="8" fill="#E53E3E"/>
  
  <!-- Yan çizgiler -->
  <polygon points="10,40 30,60 30,160 10,180" fill="#E53E3E"/>
  <polygon points="310,40 330,60 330,160 310,180" fill="#E53E3E"/>
</svg>'''
    
    return svg_content

def create_mtb_logo_png():
    """MTB logosunu PNG formatında oluştur (PIL kullanarak)"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 400x200 boyutunda beyaz arka plan
        img = Image.new('RGBA', (400, 200), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Kırmızı renk
        red_color = (229, 62, 62, 255)
        
        # M harfi
        m_points = [(20,50), (20,150), (40,150), (40,80), (60,120), (80,80), (80,150), (100,150), (100,50), (80,50), (60,90), (40,50)]
        # M harfini çizmek için parçalara böl
        draw.rectangle([20, 50, 40, 150], fill=red_color)  # Sol dikey
        draw.rectangle([80, 50, 100, 150], fill=red_color)  # Sağ dikey
        draw.polygon([(40, 50), (60, 90), (50, 50)], fill=red_color)  # Sol çapraz
        draw.polygon([(60, 90), (80, 50), (70, 50)], fill=red_color)  # Sağ çapraz
        
        # T harfi
        draw.rectangle([120, 50, 200, 70], fill=red_color)  # Üst yatay
        draw.rectangle([150, 50, 170, 150], fill=red_color)  # Dikey
        
        # B harfi - basitleştirilmiş
        draw.rectangle([220, 50, 240, 150], fill=red_color)  # Sol dikey
        draw.rectangle([240, 50, 290, 70], fill=red_color)   # Üst yatay
        draw.rectangle([240, 90, 285, 110], fill=red_color)  # Orta yatay
        draw.rectangle([240, 130, 295, 150], fill=red_color) # Alt yatay
        draw.rectangle([270, 70, 290, 90], fill=red_color)   # Üst sağ dikey
        draw.rectangle([275, 110, 295, 130], fill=red_color) # Alt sağ dikey
        
        # Alt çizgi
        draw.rectangle([20, 160, 300, 168], fill=red_color)
        
        # Yan çizgiler
        draw.polygon([(10, 40), (30, 60), (30, 160), (10, 180)], fill=red_color)
        draw.polygon([(310, 40), (330, 60), (330, 160), (310, 180)], fill=red_color)
        
        return img
        
    except ImportError:
        print("PIL paketi bulunamadı. Logo oluşturulamadı.")
        return None

if __name__ == "__main__":
    # PNG logo oluştur
    logo = create_mtb_logo_png()
    if logo:
        logo.save("mtb_logo.png")
        print("MTB logosu mtb_logo.png olarak kaydedildi")
    
    # SVG logo oluştur
    svg_content = create_mtb_logo_svg()
    with open("mtb_logo.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("MTB logosu mtb_logo.svg olarak kaydedildi")