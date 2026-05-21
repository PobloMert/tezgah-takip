import sqlite3
from datetime import datetime

class CloudDatabaseModels:
    """Bulut tabanlı çok kullanıcılı sistem için genişletilmiş veritabanı şeması"""
    
    @staticmethod
    def get_schema_queries():
        return [
            # Organizasyonlar (Şirketler/Fabrikalar)
            """CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Kullanıcılar
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT CHECK(role IN ('admin', 'editor', 'viewer')) DEFAULT 'viewer',
                full_name TEXT,
                email TEXT,
                last_login TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )""",
            
            # Tezgahlar (organization_id eklendi)
            """CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                name TEXT NOT NULL,
                model TEXT,
                status TEXT,
                last_maintenance DATE,
                next_maintenance DATE,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )""",
            
            # Veri Paylaşım Kayıtları (Kim hangi dosyayı/tezgahı görebilir - Opsiyonel detay)
            """CREATE TABLE IF NOT EXISTS data_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER,
                user_id INTEGER,
                permission_level TEXT,
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )"""
        ]

    @staticmethod
    def initialize_cloud_db(db_path="tezgah_takip_cloud.db"):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for query in CloudDatabaseModels.get_schema_queries():
            cursor.execute(query)
        conn.commit()
        conn.close()

if __name__ == "__main__":
    CloudDatabaseModels.initialize_cloud_db()
    print("Bulut uyumlu veritabanı şeması başarıyla oluşturuldu.")
