
import random
from PyQt5 import uic,QtWidgets
from PyQt5.QtWidgets import QWidget
from db import DataBase
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QHBoxLayout

from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtCore import Qt

class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DataBase()

        uic.loadUi("admin_dashboard.ui", self)

        # ربط الأزرار من الواجهة
        self.addEmployeeBtn.clicked.connect(self.open_add_user_window)
        self.logoutBtn.clicked.connect(self.log_out)
        self.showMaximized()
        QFontDatabase.addApplicationFont("fonts/Alyamama-Bold.ttf")
        
        self.setStyleSheet("""
    * {
        font-family: "Alyamama";
        color: white;
    }
""")
        self.employeesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


        self.db.cur.execute("""
            SELECT 
                username,
                password,
                full_name,
                email,
                phone,
                status,
                role.role_name
            FROM users
            JOIN role ON users.role_id = role.role_id
            """)

        result = self.db.cur.fetchall()
        for user in result: 
            row_position = self.employeesTable.rowCount()
            self.employeesTable.insertRow(row_position)

            self.employeesTable.setItem(row_position, 0, QTableWidgetItem((user[0])))
            self.employeesTable.setItem(row_position, 1, QTableWidgetItem((user[1])))
            self.employeesTable.setItem(row_position, 2, QTableWidgetItem((user[2])))
            self.employeesTable.setItem(row_position, 3, QTableWidgetItem((user[3])))
            self.employeesTable.setItem(row_position, 4, QTableWidgetItem((user[4])))
            self.employeesTable.setItem(row_position, 5, QTableWidgetItem((user[5])))
            self.employeesTable.setItem(row_position, 6, QTableWidgetItem(str(user[6])))




    def open_add_user_window(self):
        self.adduser_window = AddUserWindow(self)  #  مرّر الكائن نفسه
        self.adduser_window.show()


    def add_row(self, username, password,full_name,email,phone,status,role_id):
        row_position = self.employeesTable.rowCount()
        self.employeesTable.insertRow(row_position)

        self.employeesTable.setItem(row_position, 0, QTableWidgetItem(username))
        self.employeesTable.setItem(row_position, 1, QTableWidgetItem(password))
        self.employeesTable.setItem(row_position, 2, QTableWidgetItem(full_name))
        self.employeesTable.setItem(row_position, 3, QTableWidgetItem(email))
        self.employeesTable.setItem(row_position, 4, QTableWidgetItem(phone))
        self.employeesTable.setItem(row_position, 5, QTableWidgetItem(status))
        self.employeesTable.setItem(row_position, 6, QTableWidgetItem(role_id))

    def log_out (self):
        self.close()

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QMessageBox
)
from PyQt5.QtCore import Qt
import os
from db import DataBase
from datetime import date

class UserWindow(QWidget):
    def __init__(self, current_user_id):
        super().__init__()
        self.current_user_id = current_user_id
        self.db = DataBase()

        self.setWindowTitle("User Dashboard")
        self.setFixedSize(950, 900)

        # Title
        self.title = QLabel("Welcome to the program ❤️")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setObjectName("titleLabel")

        # Buttons
        self.new_case = QPushButton("New Case")
        self.new_case.clicked.connect(self.new_case_dialog)

        self.documents = QPushButton("Documents")
        self.documents.clicked.connect(self.show_documents)

        self.client = QPushButton("Client")
        self.client.clicked.connect(self.show_clients)

        # Client Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Plaintiff Name", "Plaintiff ID", "Plaintiff Phone",
            "Defendant Name", "Defendant ID", "Defendant Phone",
            "Defendant Address", "Case Type"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.hide()

        # Documents Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.files_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.files_widget.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.files_widget)
        self.scroll_area.hide()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.new_case)
        layout.addWidget(self.documents)
        layout.addWidget(self.client)
        layout.addWidget(self.table)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        with open("style.qss", "r") as f:
            self.setStyleSheet(f.read())

    # ================= CLIENT =================
    def show_clients(self):
        self.scroll_area.hide()
        self.table.show()
        self.load_clients()

    def load_clients(self):
        self.table.setRowCount(0)
        db = DataBase()
        db.cur.execute("""
            SELECT 
                client_id,
                plaintiff_name,
                plaintiff_national_id,
                plaintiff_phone,
                defendant_name,
                defendant_national_id,
                defendant_phone,
                defendant_address,
                case_type
            FROM cms.client
        """)
        clients = db.cur.fetchall()
        db.close()

        self.table.setRowCount(len(clients))
        for row, client in enumerate(clients):
            for col, value in enumerate(client[1:]):  # عرض كل شيء ما عدا client_id
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    # ================= DOCUMENTS =================
    def show_documents(self):
        self.table.hide()
        self.scroll_area.show()

        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        db = DataBase()
        db.cur.execute("""
            SELECT d.file_path
            FROM cms.file_transfer ft
            JOIN cms.document d ON ft.document_id = d.document_id
            WHERE ft.receiver_id = %s
            ORDER BY ft.transfer_date DESC
        """, (self.current_user_id,))
        files = db.cur.fetchall()
        db.close()

        row = col = 0
        for (file_path,) in files:
            card = QWidget()
            card_layout = QVBoxLayout(card)

            icon = QLabel("📄")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("font-size: 40px;")

            name = QLabel(os.path.basename(file_path))
            name.setAlignment(Qt.AlignCenter)
            name.setWordWrap(True)

            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda checked, p=file_path: self.open_file(p))

            card_layout.addWidget(icon)
            card_layout.addWidget(name)
            card_layout.addWidget(open_btn)

            self.grid_layout.addWidget(card, row, col)

            col += 1
            if col == 4:
                col = 0
                row += 1

    def open_file(self, file_path):
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            QMessageBox.warning(self, "Error", "File not found")

    # ================= NEW CASE =================
    def new_case_dialog(self):
        db = DataBase()

        # جلب كل العملاء
        db.cur.execute("""
            SELECT client_id, plaintiff_name, case_type
            FROM cms.client
        """)
        clients = db.cur.fetchall()
        db.close()

        if not clients:
            QMessageBox.information(self, "Info", "No clients found in the database.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Case")
        dialog.setFixedSize(450, 300)
        layout = QVBoxLayout(dialog)

        label = QLabel("اختر لائحة الدعوى:")
        layout.addWidget(label)

        # جدول اختيار العميل
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Client Name", "Case Type"])
        table.setRowCount(len(clients))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row, client in enumerate(clients):
            client_id, name, case_type = client
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(case_type))
        layout.addWidget(table)

        save_btn = QPushButton("Create Case")
        layout.addWidget(save_btn)

        def create_case():
            selected_rows = table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(dialog, "Warning", "اختر لائحة أولاً")
                return
            row_idx = selected_rows[0].row()
            client_id, name, case_type = clients[row_idx]

            # 1️⃣ إنشاء رقم القضية
            case_number = f"CASE-{date.today().strftime('%Y%m%d')}-{row_idx+1}"
            filing_date = date.today()
            status = "Open"

            db = DataBase()
            # 2️⃣ إدراج القضية
            db.cur.execute("""
                INSERT INTO cms.court_case (case_type, case_number, status, filing_date, created_by)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING case_id
            """, (case_type, case_number, status, filing_date, self.current_user_id))
            new_case_id = db.cur.fetchone()[0]

            # 3️⃣ ربط العميل بالقضية في case_client
            db.cur.execute("""
                INSERT INTO cms.case_client (case_id, client_id, role_in_case)
                VALUES (%s, %s, %s)
            """, (new_case_id, client_id, "Plaintiff"))

            # 4️⃣ ربط المستندات بالقضية حسب case_type
            db.cur.execute("""
                UPDATE cms.document
                SET case_id = %s
                WHERE uploaded_by = %s AND case_id IS NULL AND document_type = %s
            """, (new_case_id, self.current_user_id, case_type))

            db.conn.commit()
            db.close()

            QMessageBox.information(dialog, "Success", f"Case created successfully with ID {new_case_id}")
            dialog.accept()

        save_btn.clicked.connect(create_case)
        dialog.exec_()




class AddUserWindow(QMainWindow):
    def __init__(self, admin_window):
        super().__init__()
        self.admin = admin_window
        uic.loadUi("add_user.ui", self)  # افترض وجود الواجهة

        # جلب البيانات من جدول role
        self.db = DataBase()
        self.role_combo.clear()
        self.db.cur.execute("SELECT role_id, role_name FROM role")
        roles = self.db.cur.fetchall()
        for role in roles:
            role_id, role_name = role
            self.role_combo.addItem(role_name, role_id)
        self.setStyleSheet("""
        * {
            font-family: "Alyamama";
            color: #452829;
        }
    """)
        # ملء حالة الموظف في combo
        self.status_combo.clear()
        self.status_combo.addItem("اختر الحالة")  # placeholder
        self.status_combo.addItem("ACTIVE")
        self.status_combo.addItem("INACTIVE")

        # تكبير الحقول
        for widget in [self.username_input, self.password_input, self.full_name_input,
                       self.email_input, self.phone_input, self.status_combo, self.role_combo]:
            widget.setMinimumHeight(35)

        # ترتيب Status + Role جنب بعض
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.status_combo)
        horizontal_layout.addWidget(self.role_combo)

        # نحذفهم من الـ layout القديم لو موجودين
        self.mainLayout.removeWidget(self.status_combo)
        self.mainLayout.removeWidget(self.role_combo)

        # نضيفهم قبل زر الحفظ
        index_save_btn = self.mainLayout.indexOf(self.saveBtn)
        self.mainLayout.insertLayout(index_save_btn, horizontal_layout)

        # ربط زر الحفظ
        self.saveBtn.clicked.connect(self.add_user_to_db)

    def add_user_to_db(self):
        username = self.username_input.text()
        password = self.password_input.text()
        full_name = self.full_name_input.text()
        email = self.email_input.text()
        phone = self.phone_input.text()

        # التحقق من اختيار الحالة
        if self.status_combo.currentIndex() == 0:
            QMessageBox.warning(self, "تحذير", "اختر حالة صالحة!")
            return
        status = self.status_combo.currentText()

        # جلب role_id من combo
        role_id = self.role_combo.currentData()

        # إدخال الموظف في قاعدة البيانات
        user_id = random.randint(20260000, 20269999)
        self.db.cur.execute(
            "INSERT INTO users (user_id, username, password, full_name, email, phone, status, role_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (user_id, username, password, full_name, email, phone, status, role_id)
        )
        self.db.conn.commit()
        self.db.close()

        # تحديث جدول الموظفين في الواجهة الرئيسية
        self.admin.add_row(username, password, full_name, email, phone, status, self.role_combo.currentText())

        QMessageBox.information(self, "نجاح", "تم إضافة المستخدم بنجاح")
        self.close()

class Petition_Clerks(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DataBase()

        # تحميل الواجهة من ملف UI
        uic.loadUi("petition_clerks2.ui", self)  
        self.showMaximized()
        self.setStyleSheet("""
        * {
            font-family: "Alyamama";
            color: #452829;
        }
    """)

        # ربط زر أو أكثر لفتح صفحة التسجيل
        # self.case_present_alimony.clicked.connect(self.register_client)
        # self.case_absent_alimony.clicked.connect(self.register_client)
        # self.case_present_furniture.clicked.connect(self.register_client)
        # self.case_absent_furniture.clicked.connect(self.register_client)
        # self.case_present_dowry.clicked.connect(self.register_client)
        # self.case_absent_dowry.clicked.connect(self.register_client)
    
    def register_client (self):

        self.register_petitions = Register_petitions()
        self.register_petitions.show()

class Register_petitions (QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(550, 500)

        # عناصر الواجهة
        self.title = QLabel("Register_Client")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setObjectName("inputField")

        self.plaintiff_name = QLineEdit()
        self.plaintiff_name.setPlaceholderText("plaintiff name")
        self.plaintiff_name.setObjectName("inputField")

        self.plaintiff_national_id = QLineEdit()
        self.plaintiff_national_id.setPlaceholderText("plaintiff national id")
        self.plaintiff_national_id.setObjectName("inputField")

        self.plaintiff_phone = QLineEdit()
        self.plaintiff_phone.setPlaceholderText("plaintiff phone")
        self.plaintiff_phone.setObjectName("inputField")

        self.defendant_name = QLineEdit()
        self.defendant_name.setPlaceholderText("defendant name")
        self.defendant_name.setObjectName("inputField")

        self.defendant_national_id = QLineEdit()
        self.defendant_national_id.setPlaceholderText("defendant national id")
        self.defendant_national_id.setObjectName("inputField")

        self.defendant_phone = QLineEdit()
        self.defendant_phone.setPlaceholderText("defendant phone")
        self.defendant_phone.setObjectName("inputField")

        self.defendant_address = QLineEdit()
        self.defendant_address.setPlaceholderText("defendant address")
        self.defendant_address.setObjectName("inputField")

        self.case_type = QLineEdit()
        self.case_type.setPlaceholderText("case type")
        self.case_type.setObjectName("inputField")




        self.Register_Client_btn = QPushButton("Register Client")
        self.Register_Client_btn.setObjectName("Register_Client")
        self.Register_Client_btn.clicked.connect(self.Register_Client_to_db)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.plaintiff_name)
        layout.addWidget(self.plaintiff_national_id)
        layout.addWidget(self.plaintiff_phone)
        layout.addWidget(self.defendant_name)
        layout.addWidget(self.defendant_phone)
        layout.addWidget(self.defendant_national_id)
        layout.addWidget(self.defendant_address)
        layout.addWidget(self.case_type)

        layout.addWidget(self.Register_Client_btn)

        self.setLayout(layout)

        # تحميل ملف الستايل QSS
        with open("style.qss", "r") as f:
            self.setStyleSheet(f.read())
    
    def Register_Client_to_db(self):
        id = random.randint(0,10000000)
        print(id)
        plaintiff_name = self.plaintiff_name.text()
        plaintiff_national_id = self.plaintiff_national_id.text()
        plaintiff_phone = self.plaintiff_phone.text()
        defendant_name = self.defendant_name.text()
        defendant_national_id = self.defendant_national_id.text()
        defendant_phone = self.defendant_phone.text()
        defendant_address = self.defendant_address.text()
        case_type = self.case_type.text()

        db = DataBase()
        db.cur.execute(
            "INSERT INTO cms.client (client_id, plaintiff_name, plaintiff_national_id,plaintiff_phone,defendant_name,defendant_national_id,defendant_phone,defendant_address,case_type) " \
            "VALUES (%s, %s, %s,%s, %s, %s,%s, %s,%s)",
            (id, plaintiff_name, plaintiff_national_id,plaintiff_phone,defendant_name,defendant_national_id,defendant_phone,defendant_address,case_type)
        )
        # QMessageBox.warning(self, "User added successfully") 

        self.plaintiff_name.clear()
        self.plaintiff_national_id.clear()
        self.plaintiff_phone.clear()
        self.defendant_name.clear()
        self.defendant_national_id.clear()
        self.defendant_phone.clear()
        self.defendant_address.clear()
        self.case_type.clear()
        
        db.conn.commit()
        db.close()

        QMessageBox.information(self, "success", "Client added successfully")


        self.close() 