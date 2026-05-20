#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Gelişmiş Otomatik Güncelleyici
Setup.exe indirme ve çalıştırma desteği
"""
import requests
import os
import sys
import subprocess

class AutoUpdater:
    def __init__(self, repo_owner="PobloMert", repo_name="tezgah-takip"):
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self.current_version = "2.1.6"

    def check_for_updates(self):
        try:
            response = requests.get(self.api_url)
            if response.status_code == 200:
                data = response.json()
                latest_version = data['tag_name'].replace('v', '')
                if latest_version > self.current_version:
                    # Setup.exe var mı kontrol et
                    setup_asset = next((a for a in data['assets'] if "Setup" in a['name']), None)
                    return True, {
                        'version': latest_version,
                        'download_url': setup_asset['browser_download_url'] if setup_asset else None,
                        'notes': data.get('body', '')
                    }
            return False, None
        except Exception as e:
            print(f"Güncelleme kontrolü hatası: {e}")
            return False, None

    def download_and_apply_update(self, update_info):
        url = update_info.get('download_url')
        if not url:
            return False
        
        try:
            setup_path = os.path.join(os.environ['TEMP'], "TezgahTakip_Setup_New.exe")
            print(f"📥 Yeni sürüm indiriliyor: {url}")
            
            response = requests.get(url, stream=True)
            with open(setup_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("⚙️ Kurulum başlatılıyor...")
            # /VERYSILENT parametresi ile arka planda kurulum yapılabilir (Inno Setup desteği)
            subprocess.Popen([setup_path, "/SILENT", "/CLOSEAPPLICATIONS"], shell=True)
            return True
        except Exception as e:
            print(f"İndirme/Kurulum hatası: {e}")
            return False
