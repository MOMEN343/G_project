import sys
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication, QMessageBox
from admin import AdminWindow
from petition_clerks import Petition_Clerks
from user_window import UserWindow
from db import DataBase

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

        # Login Screen setup
        self.login_widget = QtWidgets.QWidget()
        uic.loadUi("login.ui", self.login_widget)
        self.stack.addWidget(self.login_widget)

        self.db = DataBase()   
        self.db.create_tables()

        if hasattr(self.login_widget, 'splitter'):
            # إخفاء المقبض (Handle) للـ Splitter
            self.login_widget.splitter.setHandleWidth(0)            
            # منع تغيير الحجم بواسطة المستخدم
            self.login_widget.splitter.setChildrenCollapsible(False)           
            # تعطيل خاصية السحب
            for i in range(self.login_widget.splitter.count()):
                self.login_widget.splitter.handle(i).setEnabled(False)

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
        QFontDatabase.addApplicationFont("fonts/Alyamama-Bold.ttf")
        
        # Apply Stylesheets
        self.login_widget.courtTitle.setStyleSheet("""
            * {
                font-family: "Alyamama";
                color: white;
            }
        """)
        self.login_widget.loginLabel.setStyleSheet("""
            * {
                font-family: "Alyamama";
                background-color: white;
                color:#452829;                        
            }
        """)
        self.login_widget.loginButton.setStyleSheet("""
            * {
                font-family: "Alyamama";            
                font-size: 20px         
            }
        """)

        self.showMaximized()
        QtCore.QTimer.singleShot(100, self.login_widget.username.clearFocus)

        # Set splitter sizes after showMaximized to ensure correct calculation
        if hasattr(self.login_widget, 'splitter'):
            # Get the available width after maximization
            screen_width = self.width()
            half_width = screen_width // 2
            self.login_widget.splitter.setSizes([half_width, half_width])

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # لو ضغط خارج الحقول
            if not (self.login_widget.username.geometry().contains(event.pos()) or 
                    self.login_widget.password.geometry().contains(event.pos())):
                self.login_widget.username.clearFocus()
                self.login_widget.password.clearFocus()
        return super().eventFilter(obj, event)

    def handle_login(self):
        us = self.login_widget.username.text()
        ps = self.login_widget.password.text()

        self.db.cur.execute(
                "SELECT * FROM cms.users WHERE username = %s AND password = %s",
                (us, ps)
            )
        result = self.db.cur.fetchone()

        if result != None :
            # Clear any previous dashboard widgets
            for i in range(self.stack.count() - 1, 0, -1):
                widget = self.stack.widget(i)
                self.stack.removeWidget(widget)
                widget.deleteLater()

            if us == (result[1]) and ps == (result[2]) and (result[7] == 1) :
                self.admin_dashboard = AdminWindow(main_shell=self)
                self.stack.addWidget(self.admin_dashboard)
                self.stack.setCurrentWidget(self.admin_dashboard)
                self.login_widget.username.clear()
                self.login_widget.password.clear()

            elif us == result[1] and ps == result[2] and (result[7] == 2)  :
                self.user_dashboard = UserWindow(result[0], main_shell=self)
                self.stack.addWidget(self.user_dashboard)
                self.stack.setCurrentWidget(self.user_dashboard)
                self.login_widget.username.clear()
                self.login_widget.password.clear()

            elif us == result[1] and ps == result[2] and (result[7] == 3)  :
                self.petition_clerk_dashboard = Petition_Clerks(result[0], main_shell=self)
                self.stack.addWidget(self.petition_clerk_dashboard)
                self.stack.setCurrentWidget(self.petition_clerk_dashboard)
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

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())