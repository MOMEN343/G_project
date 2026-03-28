import sys
import os
import bcrypt
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication, QMessageBox

def resource_path(relative_path):
    """ جلب المسار المطلق للموارد، يعمل في التطوير وفي PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from admin import AdminWindow
from petition_clerks import Petition_Clerks
from user_window import UserWindow
from judge_window import JudgeWindow
from db import DataBase
from modern_login import ModernLoginWidget

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("المحكمة الشرعية")
        # Main widget and layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Stacked Widget
        self.stack = QtWidgets.QStackedWidget()
        self.layout.addWidget(self.stack)

        # Login Screen setup (Modern Version)
        self.login_widget = ModernLoginWidget()
        self.stack.addWidget(self.login_widget)

        self.db = DataBase()   
        self.db.create_tables()

        self.login_widget.installEventFilter(self)
        self.login_widget.cardLayout.setSpacing(10)
        self.login_widget.loginButton.clicked.connect(self.handle_login)
       
        # Fix Tab Order
        self.login_widget.username.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.login_widget.password.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.login_widget.loginButton.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        QtWidgets.QWidget.setTabOrder(self.login_widget.username, self.login_widget.password)
        QtWidgets.QWidget.setTabOrder(self.login_widget.password, self.login_widget.loginButton)

        # Triger login on Enter key
        self.login_widget.username.returnPressed.connect(self.handle_login)
        self.login_widget.password.returnPressed.connect(self.handle_login)
        self.login_widget.loginButton.setAutoDefault(True)
        self.login_widget.loginButton.setDefault(True)
        
        # Load fonts
        QFontDatabase.addApplicationFont(resource_path("fonts/Alyamama-Bold.ttf"))
        

        self.showMaximized()
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            click_pos = event.pos()
            user_rect = self.login_widget.username.rect()
            user_pos = self.login_widget.username.mapTo(self.login_widget, QtCore.QPoint(0,0))
            pass_rect = self.login_widget.password.rect()
            pass_pos = self.login_widget.password.mapTo(self.login_widget, QtCore.QPoint(0,0))

            on_user = user_rect.translated(user_pos).contains(click_pos)
            on_pass = pass_rect.translated(pass_pos).contains(click_pos)

            if not (on_user or on_pass):
                self.login_widget.username.clearFocus()
                self.login_widget.password.clearFocus()
        return super().eventFilter(obj, event)

    def handle_login(self):
        us = self.login_widget.username.text()
        ps = self.login_widget.password.text()

        self.db.cur.execute(
                "SELECT * FROM cms.users WHERE username = %s AND status != 'DELETED'",
                (us,)
            )
        result = self.db.cur.fetchone()

        # التحقق من وجود المستخدم ثم مطابقة الهاش
        if result is not None:
            stored_password = result[2]
            try:
                # التحقق مما إذا كانت كلمة المرور المدخلة تطابق الهاش المخزن
                is_valid = bcrypt.checkpw(ps.encode('utf-8'), stored_password.encode('utf-8'))
            except Exception:
                is_valid = (ps == stored_password)

            if is_valid:
                # Clear any previous dashboard widgets
                for i in range(self.stack.count() - 1, 0, -1):
                    widget = self.stack.widget(i)
                    self.stack.removeWidget(widget)
                    widget.deleteLater()

                if us == (result[1]) and (result[7] == 1):
                    self.admin_dashboard = AdminWindow(main_shell=self)
                    self.stack.addWidget(self.admin_dashboard)
                    self.stack.setCurrentWidget(self.admin_dashboard)
                    self.login_widget.username.clear()
                    self.login_widget.password.clear()

                elif us == result[1] and (result[7] == 2):
                    self.user_dashboard = UserWindow(result[0], main_shell=self)
                    self.stack.addWidget(self.user_dashboard)
                    self.stack.setCurrentWidget(self.user_dashboard)
                    self.login_widget.username.clear()
                    self.login_widget.password.clear()

                elif us == result[1] and (result[7] == 3):
                    self.petition_clerk_dashboard = Petition_Clerks(result[0], main_shell=self)
                    self.stack.addWidget(self.petition_clerk_dashboard)
                    self.stack.setCurrentWidget(self.petition_clerk_dashboard)
                    self.login_widget.username.clear()
                    self.login_widget.password.clear()

                elif us == result[1] and (result[7] == 4):
                    self.judge_dashboard = JudgeWindow(result[0], main_shell=self)
                    self.stack.addWidget(self.judge_dashboard)
                    self.stack.setCurrentWidget(self.judge_dashboard)
                    self.login_widget.username.clear()
                    self.login_widget.password.clear()

            else:
                # Wrong password but user exists
                QMessageBox.warning(self, "خطأ في تسجيل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.")
                self.login_widget.username.clear()
                self.login_widget.password.clear()

        else:
            QMessageBox.warning(self, "خطأ في تسجيل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.") 
            self.login_widget.username.clear()
            self.login_widget.password.clear()

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_widget)
        # Clean up dashboard widgets
        for i in range(self.stack.count() - 1, 0, -1):
            widget = self.stack.widget(i)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def closeEvent(self, event):
        try:
            success, msg = self.db.backup_database()
            if success:
                print("Automatic Backup Success upon closing.")
            else:
                print("Automatic Backup Failed:", msg)
        except Exception as e:
            print("Automatic Backup Exception:", e)
        super().closeEvent(event)

app = QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec_())