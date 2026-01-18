import sys
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication, QMessageBox
from admin import AdminWindow, Petition_Clerks, UserWindow
from db import DataBase

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("login.ui", self)    
        self.db = DataBase()   

        self.splitter.setSizes([self.width()//2, self.width()//2]) 
        if hasattr(self, 'splitter'):
        # إخفاء المقبض (Handle) للـ Splitter
            self.splitter.setHandleWidth(0)            
            # منع تغيير الحجم بواسطة المستخدم
            self.splitter.setChildrenCollapsible(False)           
            # تعطيل خاصية السحب
            for i in range(self.splitter.count()):
                self.splitter.handle(i).setEnabled(False)

            self.installEventFilter(self)


        
        self.showMaximized() 
        self.cardLayout.setSpacing(10)
        self.loginButton.clicked.connect(self.handle_login)
       
        QFontDatabase.addApplicationFont("fonts/Alyamama-Bold.ttf")
        
        self.courtTitle.setStyleSheet("""
    * {
        font-family: "Alyamama";
        color: white;
    }
""")
        self.loginLabel.setStyleSheet("""
    * {
        font-family: "Alyamama";
        background-color: white;
        color:#452829;                        
    }
""")
        self.loginButton.setStyleSheet("""
    * {
        font-family: "Alyamama";            
        font-size: 20px         
    }
""")
        



    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # لو ضغط خارج الحقول
            if not (self.username.geometry().contains(event.pos()) or 
                    self.password.geometry().contains(event.pos())):
                self.username.clearFocus()
                self.password.clearFocus()
        return super().eventFilter(obj, event)

    def handle_login(self):

        us = self.username.text()
        ps = self.password.text()



        self.db.cur.execute(
                "SELECT * FROM cms.users WHERE username = %s AND password = %s",
                (us, ps)
            )
        result = self.db.cur.fetchone()

        if result != None :

            if us == (result[1]) and ps == (result[2]) and (result[7] == 1) :

                self.admin_window = AdminWindow()
                self.admin_window.show()
                self.username.clear()
                self.password.clear()

            elif us == result[1] and ps == result[2] and (result[7] == 2)  :

                self.user_window = UserWindow(result[0])
                self.user_window.show()
                self.username.clear()
                self.password.clear()

            elif us == result[1] and ps == result[2] and (result[7] == 3)  :

                self.Petition_Clerks_window = Petition_Clerks(result[0])
                self.Petition_Clerks_window.show()
                self.username.clear()
                self.password.clear()

        else:
            QMessageBox.warning(self, "خطأ في تسجيل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.") 
            self.username.clear()
            self.password.clear()



app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())