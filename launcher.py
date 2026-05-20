#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Zorunlu Güncelleme Başlatıcısı
Kullanıcıyı güncellemeyi yapmaya zorlar.
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk
from auto_updater import AutoUpdater

class MandatoryUpdateLauncher:
    def __init__(self):
        self.updater = AutoUpdater()
        self.root = tk.Tk()
        self.root.title("TezgahTakip - Güncelleme Kontrolü")
        self.root.geometry("400x200")
        self.root.withdraw() # Başlangıçta gizle

    def check_and_launch(self):
        print("🔍 Güncellemeler kontrol ediliyor...")
        update_available, update_info = self.updater.check_for_updates()
        
        if update_available:
            new_version = update_info.get('version', 'Bilinmiyor')
            response = messagebox.askyesno(
                "Yeni Güncelleme Mevcut!",
                f"Uygulamanın yeni bir sürümü (v{new_version}) mevcut.\n\n"
                "Bu güncelleme kritik iyileştirmeler içerir ve yapılması zorunludur.\n"
                "Şimdi güncellemek istiyor musunuz?\n\n"
                "(Hayır derseniz uygulama kapatılacaktır.)"
            )
            
            if response:
                print("🚀 Güncelleme başlatılıyor...")
                if self.updater.download_and_apply_update(update_info):
                    messagebox.showinfo("Başarılı", "Güncelleme başarıyla uygulandı. Uygulama yeniden başlatılıyor.")
                    # Burada Setup.exe çalıştırılabilir veya uygulama restart edilebilir
                    sys.exit(0)
                else:
                    messagebox.showerror("Hata", "Güncelleme uygulanamadı. Lütfen internet bağlantınızı kontrol edin.")
                    sys.exit(1)
            else:
                messagebox.showwarning("Zorunlu Güncelleme", "Güncelleme yapılmadan uygulama başlatılamaz.")
                sys.exit(0)
        else:
            print("✅ Uygulama güncel. Başlatılıyor...")
            self.launch_main_app()

    def launch_main_app(self):
        # Ana uygulamayı başlat
        try:
            import subprocess
            # Paketleme durumuna göre yol belirle
            if getattr(sys, 'frozen', False):
                app_path = os.path.join(os.path.dirname(sys.executable), "tezgah_takip_app.exe")
            else:
                app_path = "python tezgah_takip_app.py"
            
            subprocess.Popen(app_path, shell=True)
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Hata", f"Uygulama başlatılamadı: {e}")
            sys.exit(1)

if __name__ == "__main__":
    launcher = MandatoryUpdateLauncher()
    launcher.check_and_launch()
