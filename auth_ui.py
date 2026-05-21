from PyQt5 import QtWidgets, QtCore, QtGui

class LoginWindow(QtWidgets.QDialog):
    """Kullanıcı Giriş ve Kayıt Ekranı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TezgahTakip - Bulut Girişi")
        self.setFixedSize(400, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo veya Başlık
        title = QtWidgets.QLabel("TEZGAH TAKİP")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        subtitle = QtWidgets.QLabel("Bulut Hesabınıza Giriş Yapın")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(subtitle)
        
        # Giriş Alanları
        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("Kullanıcı Adı")
        self.username.setMinimumHeight(40)
        layout.addWidget(self.username)
        
        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("Şifre")
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setMinimumHeight(40)
        layout.addWidget(self.password)
        
        # Butonlar
        self.login_btn = QtWidgets.QPushButton("Giriş Yap")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; border-radius: 5px;")
        layout.addWidget(self.login_btn)
        
        self.register_btn = QtWidgets.QPushButton("Yeni Organizasyon Oluştur")
        self.register_btn.setFlat(True)
        self.register_btn.setStyleSheet("color: #3498db;")
        layout.addWidget(self.register_btn)
        
        layout.addStretch()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())
