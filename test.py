import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QFontDatabase
from admin import UserWindow  # Import the class to test

app = QtWidgets.QApplication(sys.argv)

# Load the font
QFontDatabase.addApplicationFont("fonts/Alyamama-Bold.ttf")

# Instantiate UserWindow with a valid user ID (e.g., from DB, or just a dummy one)
# We can use a dummy ID for UI testing.
window = UserWindow(current_user_id=20261234) # Example ID
window.show()

sys.exit(app.exec_()) 
