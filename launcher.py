#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Uygulama Başlatıcısı
Tek tıkla çalışan launcher ve güncelleme kontrolü
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading
import time
from auto_updater import AutoUpdater

class TezgahTakipLauncher:
    """TezgahTakip Launcher"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏭 TezgahTakip Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Icon ayarla (varsa)
        try:
            if os.path.exists("mtb_logo.png"):
                self.root.iconbitmap("mtb_logo.png")
        except:
            pass
        
        self.updater = AutoUpdater()
        self.setup_ui()
        
    def setup_ui(self):
        """Arayüzü oluştur"""
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Logo ve başlık
        title_label = ttk.Label(main_frame, text="🏭 TezgahTakip", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="AI Güçlü Fabrika Bakım Yönetim Sistemi", font=("Arial", 12))
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Versiyon bilgisi
        self.version_label = ttk.Label(main_frame, text=f"Versiyon: {self.updater.current_version}", font=("Arial", 10))
        self.version_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Hazır", font=("Arial", 10))
        self.status_label.grid(row=4, column=0, columnspan=2, pady=(0, 20))
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        self.launch_button = ttk.Button(button_frame, text="🚀 Uygulamayı Başlat", command=self.launch_app, width=20)
        self.launch_button.grid(row=0, column=0, padx=(0, 10))
        
        self.update_button = ttk.Button(button_frame, text="🔄 Güncelleme Kontrol", command=self.check_updates, width=20)
        self.update_button.grid(row=0, column=1, padx=(10, 0))
        
        # Otomatik güncelleme checkbox
        self.auto_update_var = tk.BooleanVar(value=True)
        auto_update_check = ttk.Checkbutton(main_frame, text="Başlangıçta otomatik güncelleme kontrol et", 
                                          variable=self.auto_update_var)
        auto_update_check.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        # Log alanı
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=8, width=60, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Başlangıçta otomatik kontrol
        if self.auto_update_var.get():
            self.root.after(1000, self.check_updates_silent)
    
    def log(self, message):
        """Log mesajı ekle"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_status(self, status):
        """Status güncelle"""
        self.status_label.config(text=status)
        self.root.update()
    
    def update_progress(self, value):
        """Progress bar güncelle"""
        self.progress['value'] = value
        self.root.update()
    
    def check_updates_silent(self):
        """Sessiz güncelleme kontrolü"""
        def check_thread():
            try:
                self.update_status("Güncellemeler kontrol ediliyor...")
                self.log("🔍 Güncellemeler kontrol ediliyor...")
                
                update_info = self.updater.check_for_updates()
                
                if update_info['available']:
                    self.log(f"🎉 Yeni versiyon mevcut: v{update_info['version']}")
                    self.update_status(f"Yeni versiyon mevcut: v{update_info['version']}")
                    
                    # Kullanıcıya sor
                    result = messagebox.askyesno(
                        "Güncelleme Mevcut",
                        f"Yeni versiyon mevcut: v{update_info['version']}\n\n"
                        f"Yenilikler:\n{update_info['release_notes'][:200]}...\n\n"
                        f"Şimdi güncellemek istiyor musunuz?"
                    )
                    
                    if result:
                        self.perform_update(update_info)
                    else:
                        self.log("ℹ️ Güncelleme kullanıcı tarafından iptal edildi")
                        self.update_status("Güncelleme iptal edildi")
                else:
                    self.log("✅ Uygulama güncel")
                    self.update_status("Uygulama güncel")
                    
            except Exception as e:
                self.log(f"❌ Güncelleme kontrolü hatası: {e}")
                self.update_status("Güncelleme kontrolü başarısız")
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def check_updates(self):
        """Manuel güncelleme kontrolü"""
        self.check_updates_silent()
    
    def perform_update(self, update_info):
        """Güncellemeyi gerçekleştir"""
        def update_thread():
            try:
                self.update_button.config(state='disabled')
                self.launch_button.config(state='disabled')
                
                # Yedekleme
                self.update_status("Yedekleme yapılıyor...")
                self.log("💾 Mevcut versiyon yedekleniyor...")
                self.update_progress(10)
                
                if not self.updater.backup_current_version():
                    raise Exception("Yedekleme başarısız!")
                
                # İndirme
                self.update_status("Güncelleme indiriliyor...")
                self.log("📥 Güncelleme indiriliyor...")
                self.update_progress(30)
                
                def progress_callback(progress):
                    self.update_progress(30 + (progress * 0.4))  # 30-70 arası
                
                zip_path = self.updater.download_update(update_info['download_url'], progress_callback)
                
                # Uygulama
                self.update_status("Güncelleme uygulanıyor...")
                self.log("🔄 Güncelleme uygulanıyor...")
                self.update_progress(80)
                
                if self.updater.apply_update(zip_path):
                    self.log("✅ Güncelleme başarıyla tamamlandı!")
                    self.update_status("Güncelleme tamamlandı")
                    self.update_progress(100)
                    
                    self.updater.cleanup()
                    
                    # Versiyon bilgisini güncelle
                    self.updater.current_version = update_info['version']
                    self.version_label.config(text=f"Versiyon: {update_info['version']}")
                    
                    messagebox.showinfo("Güncelleme Tamamlandı", 
                                      "Güncelleme başarıyla tamamlandı!\nUygulama yeniden başlatılacak.")
                    
                    # Yeniden başlat
                    self.restart_app()
                else:
                    raise Exception("Güncelleme uygulama başarısız!")
                    
            except Exception as e:
                self.log(f"❌ Güncelleme hatası: {e}")
                self.update_status("Güncelleme başarısız")
                
                # Geri al
                self.log("⏪ Güncelleme geri alınıyor...")
                if self.updater.rollback():
                    self.log("✅ Geri alma başarılı")
                    self.update_status("Geri alma tamamlandı")
                else:
                    self.log("❌ Geri alma başarısız!")
                    self.update_status("Geri alma başarısız")
                
                messagebox.showerror("Güncelleme Hatası", f"Güncelleme başarısız:\n{e}")
            
            finally:
                self.update_button.config(state='normal')
                self.launch_button.config(state='normal')
                self.update_progress(0)
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def launch_app(self):
        """Ana uygulamayı başlat"""
        try:
            self.log("🚀 TezgahTakip başlatılıyor...")
            self.update_status("Uygulama başlatılıyor...")
            
            # Python script olarak çalıştır
            if os.path.exists("run_tezgah_takip.py"):
                subprocess.Popen([sys.executable, "run_tezgah_takip.py"])
                self.log("✅ Uygulama başlatıldı")
                self.update_status("Uygulama başlatıldı")
                
                # Launcher'ı kapat
                self.root.after(2000, self.root.quit)
            else:
                raise FileNotFoundError("run_tezgah_takip.py bulunamadı!")
                
        except Exception as e:
            self.log(f"❌ Başlatma hatası: {e}")
            self.update_status("Başlatma başarısız")
            messagebox.showerror("Başlatma Hatası", f"Uygulama başlatılamadı:\n{e}")
    
    def restart_app(self):
        """Uygulamayı yeniden başlat"""
        try:
            # Launcher'ı yeniden başlat
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            self.log(f"❌ Yeniden başlatma hatası: {e}")
            messagebox.showerror("Yeniden Başlatma Hatası", f"Yeniden başlatma başarısız:\n{e}")
    
    def run(self):
        """Launcher'ı çalıştır"""
        self.log("🏭 TezgahTakip Launcher başlatıldı")
        self.root.mainloop()

if __name__ == "__main__":
    launcher = TezgahTakipLauncher()
    launcher.run()