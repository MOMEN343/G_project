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
        self.employeesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        QFontDatabase.addApplicationFont("fonts/Alyamama-Bold.ttf")       
        self.setStyleSheet("""
    * {
        font-family: "Alyamama";
        color: white;
    }
""")

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
import shutil
from docx import Document
from db import DataBase
from datetime import date

class UserWindow(QMainWindow):
    def __init__(self, current_user_id):
        super().__init__()
        self.current_user_id = current_user_id
        self.db = DataBase()

        # Load the new UI
        uic.loadUi("employee.ui", self)
        
        # Apply the same logic as test.py for font application if needed, 
        # or rely on the UI file's stylesheet + global font loading in app.py
        self.setStyleSheet("""
        * {
            font-family: "Alyamama", "Segoe UI Symbol";
            color: #452829;
        }
        """)

        # Connect Buttons
        # Note: In the new UI, the buttons are named 'add_case' and 'docments' (typo in UI file acknowledged)
        self.add_case.clicked.connect(self.new_case_dialog)
        self.docments.clicked.connect(self.show_documents)
        self.logoutBtn.clicked.connect(self.log_out)
        
        # The scroll area and stacked widget are now in the UI file.
        # Structure: self.mainStack -> (page_empty, page_documents)
        # self.page_documents -> scrollArea -> files_widget -> files_grid
        
        # Ensure we start at the empty page
        if hasattr(self, 'mainStack'):
             self.mainStack.setCurrentIndex(0)
             
        # Force alignment on the grid layout to prevent items from expanding to fill the whole area
        if hasattr(self, 'files_grid'):
            self.files_grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def show_documents(self):
        if hasattr(self, 'mainStack'):
            self.mainStack.setCurrentIndex(1) # Show documents page

        # Clear existing
        # Note: files_grid is loaded from UI
        if hasattr(self, 'files_grid'):
            for i in reversed(range(self.files_grid.count())):
                widget = self.files_grid.itemAt(i).widget()
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
        
        # If no files, maybe switch back to empty? Or show empty grid?
        # User said "when the button clicked to apper", implying if clicked it should show. 
        # But if empty list, page_empty might be better? 
        # Stick to showing the page, even if empty.
        
        for (file_path,) in files:
            card = QWidget()
            card.setStyleSheet("background-color: white; border-radius: 10px; padding: 10px;")
            card_layout = QVBoxLayout(card)

            icon = QLabel("📄")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("font-size: 40px; border: none;")

            name = QLabel(os.path.basename(file_path))
            name.setAlignment(Qt.AlignCenter)
            name.setWordWrap(True)
            name.setStyleSheet("color: black; border: none;")

            open_btn = QPushButton("Open")
            open_btn.setStyleSheet("""
                QPushButton {
                    background-color: #452829; 
                    color: white; 
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #f3db93;
                    color: black;
                }
            """)
            open_btn.clicked.connect(lambda checked, p=file_path: self.open_file(p))

            card_layout.addWidget(icon)
            card_layout.addWidget(name)
            card_layout.addWidget(open_btn)

            self.files_grid.addWidget(card, row, col)

            col += 1
            if col == 4:
                col = 0
                row += 1

    def open_file(self, file_path):
        try:
            abs_path = os.path.abspath(file_path)
            if os.path.exists(abs_path):
                os.startfile(abs_path)
            else:
                QMessageBox.warning(self, "Error", f"File not found at:\n{abs_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {e}")
            
    def log_out(self):
        self.close()


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
    def __init__(self, current_user_id):
        super().__init__()
        self.db = DataBase()
        self.c_u_i = current_user_id
        self.current_case_data = None # To store selected case config

        # تحميل الواجهة من ملف UI
        uic.loadUi("petition_clerks2.ui", self)  
        self.showMaximized()
        self.setStyleSheet("""
        * {
            font-family: "Alyamama";
            color: #452829;
        }
    """)
        
        # Connect main buttons
        self.sendFile.clicked.connect(self.process_full_workflow)
        self.logoutBtn.clicked.connect(self.log_out)
        
        # Case Configurations
        self.case_config = {
            "case1": {"label": "نفقة زوجة", "template": "nafqa.docx"},
            "case2": {"label": "عفش بيت", "template": "nafqa.docx"}, 
            "case3": {"label": "مهر مؤجل", "template": "nafqa.docx"},
            "case4": {"label": "نفقة عفش غيابي", "template": "nafqa.docx"},
            "case5": {"label": "نفقة زوجة غيابي", "template": "nafqa.docx"},
            "case6": {"label": "نفقة صغار", "template": "nafqa.docx"},
        }

        # Case Selection Buttons
        self.buttons = [self.case1, self.case2, self.case3]
        # Try to add other buttons if they exist in UI but aren't in list yet, or stick to list
        # The user's earlier list had up to case6, but snippet showed 3. 
        # I'll rely on the buttons list and ensure the mapping handles them.
        
        for btn in self.buttons:
            btn.clicked.connect(self.handle_case_selection)

        # Populate Receivers
        self.load_receivers()

    def handle_case_selection(self):
        sender = self.sender()
        if sender:
            btn_name = sender.objectName()
            if btn_name in self.case_config:
                self.current_case_data = self.case_config[btn_name]
                # Store the key or label as the case_type for DB?
                # Usually text is better for readability unless there's an enum.
                # using label for display and DB
                self.current_case_type = self.current_case_data["label"] 
                self.label_2.setText(f"أدخل بيانات {self.current_case_type}")
            else:
                self.current_case_type = sender.text() # Fallback
                self.current_case_data = {"label": sender.text(), "template": "nafqa.docx"}
                self.label_2.setText(f"أدخل بيانات {self.current_case_type}")

    def load_receivers(self):
        self.comboBox.clear()
        self.comboBox.addItem("اختر المستلم")
        self.db.cur.execute("SELECT user_id, full_name FROM cms.users WHERE role_id = '2'")
        users = self.db.cur.fetchall()
        for user in users:
            self.comboBox.addItem(user[1], user[0])

    def process_full_workflow(self):
        # Validation
        if not self.current_case_data:
            QMessageBox.warning(self, "Error", "الرجاء اختيار نوع القضية أولاً!")
            return

        receiver_id = self.comboBox.currentData()
        if receiver_id is None:
             QMessageBox.warning(self, "Error", "الرجاء اختيار المستلم!")
             return

        # 1. Register Client
        try:
            self.client_id = random.randint(1, 10000000)
            # Re-open DB connection for transaction
            db = DataBase()
            db.cur.execute("""
                INSERT INTO cms.client (client_id, plaintiff_name, plaintiff_national_id, plaintiff_phone,
                                        defendant_name, defendant_national_id, defendant_phone, defendant_address, case_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.client_id,
                self.plaintiff_name.text(),
                self.plaintiff_national_id.text(),
                self.plaintiff_phone.text(),
                self.defendant_name.text(),
                self.defendant_national_id.text(),
                self.defendant_phone.text(),
                self.defendant_address.text(),
                self.current_case_type 
            ))
            db.conn.commit()
            db.close()
        except Exception as e:
             QMessageBox.warning(self, "Error", f"Failed to register client: {str(e)}")
             return

        # 2. Generate File
        template_name = self.current_case_data.get("template", "nafqa.docx")
        template_path = f"./file/{template_name}" 
        if not os.path.exists(template_path):
            QMessageBox.warning(self, "Error", "Original template not found!")
            return

        final_dir = os.path.abspath("./file")
        os.makedirs(final_dir, exist_ok=True)
        # Sanitize filename: Use only Client ID to avoid encoding issues on Windows
        # Or if we must include name, ensure it works. But explicit ID is safest.
        # Let's try to include name but stripped of problematic chars?
        # The user's error showed mojibake, likely due to arabic.
        # Safest is just ID or strict alphanumeric.
        # Let's stick to ID + simple timestamp or just ID.
        final_file = os.path.join(final_dir, f"final_{self.client_id}.docx")
        
        try:
            shutil.copy(template_path, final_file)
            doc = Document(final_file)
            
            days_map = {
                "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين", "Tuesday": "الثلاثاء",
                "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"
            }
            day_in_arabic = days_map.get(date.today().strftime("%A"), date.today().strftime("%A"))

            placeholders = {
                "{DATE_DAY}": day_in_arabic,
                "{DATE_FULL}": date.today().strftime("%d/%m/%Y"),
                "{PLAINTIFF_NAME}": self.plaintiff_name.text(),
                "{PLAINTIFF_ADDRESS}": "غزة معسكر الشاطئ", 
                "{LAWYER_NAME}": "معتصم كريزم",             
                "{CLERK_NAME}": "مؤمن كريزم",               
                "{DEFENDANT_NAME}": self.defendant_name.text(),
                "{DEFENDANT_ADDRESS}": self.defendant_address.text(),
                "{CONTACT_PERSON}": "أحمد محمود",           
                "{CONTRACT_DATE}": "18/2/2013",             
                "{INCOME}": "1000",                          
                "{PROPERTIES}": "خمس عقارات",               
                "{PROPERTY_INCOME}": "100000 $",             
                "{TOTAL_INCOME}": "11110000",                
                "{COURT_NAME}": "محكمة الشجاعية",           
                "{COURT_ADDRESS}": "غزة شارع النصر",        
                "{SESSION_DATE}": "9/11/2021",              
            }

            def replace_placeholders(doc, placeholders):
                for p in doc.paragraphs:
                    for run in p.runs:
                        for key, val in placeholders.items():
                            if key in run.text:
                                run.text = run.text.replace(key, val)
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for p in cell.paragraphs:
                                for run in p.runs:
                                    for key, val in placeholders.items():
                                        if key in run.text:
                                            run.text = run.text.replace(key, val)

            replace_placeholders(doc, placeholders)
            doc.save(final_file)
            
             # Save to DB
            db = DataBase()
            case_id = 1 
            db.cur.execute("""
                INSERT INTO cms.document (document_type, file_path, uploaded_by,case_id)
                VALUES (%s, %s, %s, %s)
                RETURNING document_id
            """, (self.current_case_type, final_file, self.c_u_i, case_id))
            self.document_id = db.cur.fetchone()[0]
            db.conn.commit()
            db.close()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate file: {str(e)}")
            return

        # 3. Send File (File Transfer)
        try:
            db = DataBase()
            transfer_id = random.randint(1, 1000000)
            transfer_date = date.today()
            status = "pending"

            db.cur.execute("""
                INSERT INTO cms.file_transfer (transfer_id, transfer_date, status, document_id, sender_id, receiver_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (transfer_id, transfer_date, status, self.document_id, self.c_u_i, receiver_id))

            db.conn.commit()
            db.close()
            QMessageBox.information(self, "Success", f"Client Registered, File Generated & Sent Successfully!")
            
            # Clear fields
            self.plaintiff_name.clear()
            self.plaintiff_national_id.clear()
            self.plaintiff_phone.clear()
            self.defendant_name.clear()
            self.defendant_national_id.clear()
            self.defendant_phone.clear()
            self.defendant_address.clear()
            self.comboBox.setCurrentIndex(0)
            self.current_case_type = None
            self.label_2.setText("أدخل بيانات لائحة الدعوى:")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to send file: {str(e)}")

    def log_out (self):
        self.close() 