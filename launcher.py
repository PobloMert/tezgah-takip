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

# Windows DPI awareness ayarları
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        
        # Windows DPI awareness ayarla
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (ImportError, AttributeError, OSError):
        # Fallback - eski Windows versiyonları için
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

# Enhanced Update System'i güvenli şekilde import et
try:
    from enhanced_update_manager import EnhancedUpdateManager, UpdateStatus
    from path_resolver import PathResolver
    from file_validator import FileValidator
    from backup_manager import BackupManager
    from error_handler import ErrorHandler
    from fallback_system import FallbackSystem
    from data_preservation_manager import DataPreservationManager
    from manual_update_manager import ManualUpdateManager
    ENHANCED_UPDATE_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced Update System import hatası: {e}")
    ENHANCED_UPDATE_AVAILABLE = False

# AutoUpdater'ı güvenli şekilde import et
try:
    from auto_updater import AutoUpdater
except ImportError as e:
    print(f"AutoUpdater import hatası: {e}")
    # Fallback AutoUpdater sınıfı
    class AutoUpdater:
        def __init__(self):
            self.current_version = "2.1.3"
        
        def check_for_updates(self):
            return {'available': False, 'message': 'AutoUpdater modülü yüklenemedi'}
        
        def backup_current_version(self):
            return False
        
        def download_update(self, url, callback=None):
            raise Exception("AutoUpdater modülü mevcut değil")
        
        def apply_update(self, zip_path):
            return False
        
        def cleanup(self):
            pass
        
        def rollback(self):
            return False

class TezgahTakipLauncher:
    """TezgahTakip Launcher"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏭 TezgahTakip Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Icon ayarla (varsa)
        try:
            if os.path.exists("tezgah_icon.ico"):
                self.root.iconbitmap("tezgah_icon.ico")
            elif os.path.exists("tezgah_logo.png"):
                # PNG için alternatif yöntem
                pass
        except:
            pass
        
        self.updater = AutoUpdater()
        
        # Enhanced Update System'i başlat
        if ENHANCED_UPDATE_AVAILABLE:
            self.setup_enhanced_update_system()
        
        self.setup_ui()
        
    def setup_enhanced_update_system(self):
        """Enhanced Update System'i kurulum"""
        try:
            self.path_resolver = PathResolver()
            self.file_validator = FileValidator(self.path_resolver)
            self.backup_manager = BackupManager(path_resolver=self.path_resolver)
            self.error_handler = ErrorHandler()
            self.fallback_system = FallbackSystem(self.path_resolver)
            self.data_preservation_manager = DataPreservationManager(self.path_resolver)
            self.manual_update_manager = ManualUpdateManager(self.path_resolver, self.file_validator)
            
            # Enhanced Update Manager'ı oluştur ve bileşenleri ayarla
            self.enhanced_updater = EnhancedUpdateManager()
            self.enhanced_updater.set_components(
                self.path_resolver,
                self.file_validator,
                self.backup_manager,
                self.error_handler,
                self.data_preservation_manager
            )
            
            self.log("✅ Enhanced Update System başlatıldı")
            
        except Exception as e:
            self.log(f"⚠️ Enhanced Update System başlatılamadı: {e}")
            self.enhanced_updater = None
    
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
        """Güncellemeyi gerçekleştir - Enhanced Update System ile"""
        def update_thread():
            try:
                self.update_button.config(state='disabled')
                self.launch_button.config(state='disabled')
                
                # Enhanced Update System varsa onu kullan
                if ENHANCED_UPDATE_AVAILABLE and hasattr(self, 'enhanced_updater') and self.enhanced_updater:
                    self.perform_enhanced_update(update_info)
                else:
                    self.perform_legacy_update(update_info)
                    
            except Exception as e:
                self.log(f"❌ Güncelleme hatası: {e}")
                self.update_status("Güncelleme başarısız")
                
                # Enhanced error handling varsa kullan
                if ENHANCED_UPDATE_AVAILABLE and hasattr(self, 'error_handler'):
                    error_result = self.error_handler.handle_update_error(e, {
                        'update_version': update_info.get('version', 'unknown'),
                        'update_in_progress': True
                    })
                    
                    # Manuel güncelleme seçeneği sun
                    if hasattr(self, 'manual_update_manager'):
                        self.offer_manual_update(update_info, error_result)
                else:
                    messagebox.showerror("Güncelleme Hatası", f"Güncelleme başarısız:\n{e}")
            
            finally:
                self.update_button.config(state='normal')
                self.launch_button.config(state='normal')
                self.update_progress(0)
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def perform_enhanced_update(self, update_info):
        """Enhanced Update System ile güncelleme"""
        try:
            self.log("🔧 Enhanced Update System ile güncelleme başlatılıyor...")
            self.update_status("Gelişmiş güncelleme sistemi ile güncelleniyor...")
            self.update_progress(10)
            
            # Enhanced update manager ile güncelleme yap
            target_version = update_info.get('version', '2.1.3')
            
            self.log(f"📋 Hedef versiyon: {target_version}")
            self.update_progress(20)
            
            # Güncellemeyi gerçekleştir
            update_result = self.enhanced_updater.perform_update(target_version)
            
            if update_result.success:
                self.log("✅ Enhanced güncelleme başarıyla tamamlandı!")
                self.update_status("Güncelleme tamamlandı")
                self.update_progress(100)
                
                # Versiyon bilgisini güncelle
                self.updater.current_version = target_version
                self.version_label.config(text=f"Versiyon: {target_version}")
                
                messagebox.showinfo("Güncelleme Tamamlandı", 
                                  "Güncelleme başarıyla tamamlandı!\n\n"
                                  "Uygulama yeniden başlatılacak.")
                
                self.restart_app()
            else:
                raise Exception(f"Enhanced güncelleme başarısız: {update_result.error_message}")
                
        except Exception as e:
            self.log(f"❌ Enhanced güncelleme hatası: {e}")
            raise e
    
    def perform_legacy_update(self, update_info):
        """Eski güncelleme sistemi ile güncelleme"""
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
                                      "Güncelleme başarıyla tamamlandı!\n\n"
                                      "Uygulama yeniden başlatılacak.\n"
                                      "Eğer yeniden başlatma başarısız olursa,\n"
                                      "lütfen launcher'ı manuel olarak kapatıp açın.")
                    
                    # Yeniden başlat
                    try:
                        self.restart_app()
                    except Exception as restart_error:
                        self.log(f"⚠️ Otomatik yeniden başlatma başarısız: {restart_error}")
                        messagebox.showwarning("Yeniden Başlatma", 
                                             "Otomatik yeniden başlatma başarısız.\n"
                                             "Lütfen launcher'ı manuel olarak kapatıp açın.")
                        self.update_status("Güncelleme tamamlandı - Manuel yeniden başlatma gerekli")
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
            
            # Önce executable dosyasını ara
            executable_paths = [
                "TezgahTakip.exe",  # Aynı dizinde
                os.path.join(os.path.dirname(sys.executable), "TezgahTakip.exe"),  # Launcher ile aynı dizin
                os.path.join(os.getcwd(), "TezgahTakip.exe"),  # Çalışma dizini
            ]
            
            # Python script yedek seçenek
            python_script_paths = [
                "run_tezgah_takip.py",
                "tezgah_takip_app.py",
                "main_window.py"
            ]
            
            launched = False
            
            # Önce executable'ları dene
            for exe_path in executable_paths:
                if os.path.exists(exe_path):
                    self.log(f"✅ Executable bulundu: {exe_path}")
                    subprocess.Popen([exe_path])
                    launched = True
                    break
            
            # Executable bulunamazsa Python script'lerini dene
            if not launched:
                for script_path in python_script_paths:
                    if os.path.exists(script_path):
                        self.log(f"✅ Python script bulundu: {script_path}")
                        subprocess.Popen([sys.executable, script_path])
                        launched = True
                        break
            
            if launched:
                self.log("✅ Uygulama başlatıldı")
                self.update_status("Uygulama başlatıldı")
                
                # Launcher'ı kapat
                self.root.after(2000, self.root.quit)
            else:
                raise FileNotFoundError("Ne TezgahTakip.exe ne de Python script dosyaları bulunamadı!")
                
        except Exception as e:
            self.log(f"❌ Başlatma hatası: {e}")
            self.update_status("Başlatma başarısız")
            messagebox.showerror("Başlatma Hatası", f"Uygulama başlatılamadı:\n{e}")
    
    def restart_app(self):
        """Uygulamayı yeniden başlat"""
        try:
            self.log("🔄 Launcher yeniden başlatılıyor...")
            
            # Windows'ta daha güvenli yeniden başlatma
            if sys.platform == "win32":
                # Yeni process başlat
                subprocess.Popen([sys.executable] + sys.argv)
                
                # Mevcut process'i sonlandır
                import time
                time.sleep(1)  # Yeni process'in başlaması için bekle
                self.root.quit()
                os._exit(0)
            else:
                # Linux/Mac için eski yöntem
                python = sys.executable
                os.execl(python, python, *sys.argv)
                
        except Exception as e:
            self.log(f"❌ Yeniden başlatma hatası: {e}")
            messagebox.showerror("Yeniden Başlatma Hatası", f"Yeniden başlatma başarısız:\n{e}")
            
            # Fallback: Sadece launcher'ı kapat
            self.root.quit()
    
    def run(self):
        """Launcher'ı çalıştır"""
        self.log("🏭 TezgahTakip Launcher başlatıldı")
        self.root.mainloop()

if __name__ == "__main__":
    launcher = TezgahTakipLauncher()
    launcher.run()
    
    def offer_manual_update(self, update_info, error_result):
        """Manuel güncelleme seçeneği sun"""
        try:
            self.log("🔧 Manuel güncelleme seçenekleri hazırlanıyor...")
            
            # Manuel güncelleme planı oluştur
            target_version = update_info.get('version', '2.1.3')
            error_context = {
                'error_type': 'update_failure',
                'error_message': error_result.get('error_message', 'Unknown error'),
                'update_version': target_version
            }
            
            manual_plan = self.manual_update_manager.create_manual_update_plan(target_version, error_context)
            
            # Kullanıcıya manuel güncelleme seçeneği sun
            result = messagebox.askyesno(
                "Manuel Güncelleme",
                f"Otomatik güncelleme başarısız oldu.\n\n"
                f"Manuel güncelleme talimatlarını görmek istiyor musunuz?\n\n"
                f"Tahmini süre: {manual_plan.estimated_time_minutes} dakika\n"
                f"Zorluk seviyesi: {manual_plan.difficulty_level.title()}"
            )
            
            if result:
                self.show_manual_instructions(manual_plan)
            
        except Exception as e:
            self.log(f"❌ Manuel güncelleme seçeneği hazırlanamadı: {e}")
    
    def show_manual_instructions(self, manual_plan):
        """Manuel güncelleme talimatlarını göster"""
        try:
            # Yeni pencere oluştur
            instructions_window = tk.Toplevel(self.root)
            instructions_window.title("Manuel Güncelleme Talimatları")
            instructions_window.geometry("800x600")
            instructions_window.resizable(True, True)
            
            # Ana frame
            main_frame = ttk.Frame(instructions_window, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Başlık
            title_label = ttk.Label(main_frame, text=f"Manuel Güncelleme Talimatları - v{manual_plan.target_version}", 
                                  font=("Arial", 14, "bold"))
            title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
            
            # Talimatlar metni
            instructions_text = tk.Text(main_frame, wrap=tk.WORD, font=("Consolas", 10))
            scrollbar_inst = ttk.Scrollbar(main_frame, orient="vertical", command=instructions_text.yview)
            instructions_text.configure(yscrollcommand=scrollbar_inst.set)
            
            # Talimatları yaz
            user_instructions = self.manual_update_manager.get_user_friendly_instructions(manual_plan)
            instructions_text.insert(tk.END, "\n".join(user_instructions))
            instructions_text.config(state=tk.DISABLED)
            
            instructions_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar_inst.grid(row=1, column=1, sticky=(tk.N, tk.S))
            
            # Butonlar
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
            
            ttk.Button(button_frame, text="Kapat", command=instructions_window.destroy).grid(row=0, column=0, padx=(0, 10))
            ttk.Button(button_frame, text="Talimatları Kaydet", 
                      command=lambda: self.save_instructions(user_instructions)).grid(row=0, column=1)
            
            # Grid weights
            instructions_window.columnconfigure(0, weight=1)
            instructions_window.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(1, weight=1)
            
        except Exception as e:
            self.log(f"❌ Manuel talimatlar gösterilemedi: {e}")
            messagebox.showerror("Hata", f"Manuel talimatlar gösterilemedi: {e}")
    
    def save_instructions(self, instructions):
        """Talimatları dosyaya kaydet"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Talimatları Kaydet"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("\n".join(instructions))
                
                self.log(f"✅ Talimatlar kaydedildi: {filename}")
                messagebox.showinfo("Kaydedildi", f"Talimatlar başarıyla kaydedildi:\n{filename}")
                
        except Exception as e:
            self.log(f"❌ Talimatlar kaydedilemedi: {e}")
            messagebox.showerror("Hata", f"Talimatlar kaydedilemedi: {e}")