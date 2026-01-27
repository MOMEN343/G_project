import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QFontDatabase
from admin import UserWindow 

app = QtWidgets.QApplication(sys.argv)
QFontDatabase.addApplicationFont("fonts/Alyamama-Bold.ttf")
window = UserWindow(current_user_id=20261234) 
window.show()
sys.exit(app.exec_())
