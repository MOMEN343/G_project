import random
import os
from db import DataBase
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QTableWidgetItem, 
    QVBoxLayout, QMessageBox, QHBoxLayout, QHeaderView, QCheckBox
)
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtCore import Qt

class AdminWindow(QMainWindow):
    def __init__(self, main_shell=None):
        super().__init__()
        self.main_shell = main_shell
        self.db = DataBase()

        uic.loadUi("admin_dashboard.ui", self)

        # ربط الأزرار من الواجهة
        self.addEmployeeBtn.clicked.connect(self.open_add_user_window)
        self.editEmployeeBtn.clicked.connect(self.open_edit_user_window)
        self.deleteEmployeeBtn.clicked.connect(self.delete_employee)
        self.logoutBtn.clicked.connect(self.log_out)
        
        # ربط خاصية "تحديد الكل" إذا كانت موجودة في الـ UI
        if hasattr(self, "check_all"):
            self.check_all.stateChanged.connect(self.select_all_employees)
        
        self.addEmployeeBtn.setFocusPolicy(Qt.NoFocus)
        self.deleteEmployeeBtn.setFocusPolicy(Qt.NoFocus)
        self.logoutBtn.setFocusPolicy(Qt.NoFocus)

        self.employeesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # تصغير عمود الـ checkbox
        self.employeesTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.employeesTable.setColumnWidth(0, 50)
        QFontDatabase.addApplicationFont("fonts/Alyamama-Bold.ttf")       
        self.setStyleSheet("""
    * {
        font-family: "Alyamama";
        color: white;
    }
""")

        self.db.cur.execute("""
            SELECT 
                user_id,
                username,
                password,
                full_name,
                email,
                phone,
                status,
                role.role_name
            FROM cms.users
            JOIN cms.role ON cms.users.role_id = cms.role.role_id
            """)

        # Connect search bar
        self.searchBar.textChanged.connect(self.filter_table)
        
        result = self.db.cur.fetchall()
        for user in result: 
            row_position = self.employeesTable.rowCount()
            self.employeesTable.insertRow(row_position)

            # Add checkbox in column 0
            checkbox = QCheckBox()
            checkbox_container = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.employeesTable.setCellWidget(row_position, 0, checkbox_container)
            checkbox_container.setProperty("user_id", user[0])

            # Add data items in columns 1-7
            items = [
                QTableWidgetItem(user[1]),
                QTableWidgetItem(user[2]),
                QTableWidgetItem(user[3]),
                QTableWidgetItem(user[4]),
                QTableWidgetItem(user[5]),
                QTableWidgetItem(user[6]),
                QTableWidgetItem(str(user[7]))
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.employeesTable.setItem(row_position, i + 1, item)


    def open_add_user_window(self):
        self.adduser_window = AddUserWindow(self)  #  مرّر الكائن نفسه
        self.adduser_window.show()

    def open_edit_user_window(self):
        """فتح نافذة تعديل الموظف المحدد"""
        # البحث عن السطر المحدد (الذي له checkbox مفعّل)
        selected_row = None
        selected_container = None
        selected_count = 0
        
        for row in range(self.employeesTable.rowCount()):
            # الحصول على الـ container ثم الـ checkbox منه
            container = self.employeesTable.cellWidget(row, 0)
            if container:
                checkbox = container.layout().itemAt(0).widget()
                if checkbox and checkbox.isChecked():
                    selected_row = row
                    selected_container = container
                    selected_count += 1
        
        # التحقق من تحديد موظف واحد فقط
        if selected_count == 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد موظف للتعديل")
            return
        elif selected_count > 1:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد موظف واحد فقط")
            return
        
        # جلب بيانات الموظف من الجدول
        employee_data = {
            'row': selected_row,
            'user_id': selected_container.property("user_id"),
            'username': self.employeesTable.item(selected_row, 1).text(),
            'password': self.employeesTable.item(selected_row, 2).text(),
            'fullname': self.employeesTable.item(selected_row, 3).text(),
            'email': self.employeesTable.item(selected_row, 4).text(),
            'phone': self.employeesTable.item(selected_row, 5).text(),
            'status': self.employeesTable.item(selected_row, 6).text(),
            'role': self.employeesTable.item(selected_row, 7).text()
        }
        
        # فتح نافذة الإضافة في وضع التعديل
        self.edit_window = AddUserWindow(self, employee_data)
        self.edit_window.show()
    
    def update_table_row(self, row, username, password, fullname, email, phone, status, role):
        """تحديث بيانات السطر في الجدول"""
        self.employeesTable.item(row, 1).setText(username)
        self.employeesTable.item(row, 2).setText(password)
        self.employeesTable.item(row, 3).setText(fullname)
        self.employeesTable.item(row, 4).setText(email)
        self.employeesTable.item(row, 5).setText(phone)
        self.employeesTable.item(row, 6).setText(status)
        self.employeesTable.item(row, 7).setText(role)

    def delete_employee(self):
        """حذف الموظفين المحددين"""
        ids_to_delete = []
        rows_to_delete = []
        
        for row in range(self.employeesTable.rowCount()):
            container = self.employeesTable.cellWidget(row, 0)
            if container:
                checkbox = container.layout().itemAt(0).widget()
                if checkbox and checkbox.isChecked():
                    ids_to_delete.append(container.property("user_id"))
                    rows_to_delete.append(row)
        
        if not ids_to_delete:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد موظف واحد على الأقل للحذف")
            return
            
        confirm = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف {len(ids_to_delete)} موظف؟\nهذا الإجراء لا يمكن التراجع عنه.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                db = DataBase()
                for user_id in ids_to_delete:
                    # قد نحتاج لحذف السجلات المرتبطة أولاً إذا كانت القيود تمنع الحذف المباشر
                    # لكن هنا سنحاول الحذف المباشر أولاً
                    db.cur.execute("DELETE FROM cms.users WHERE user_id = %s", (user_id,))
                
                db.conn.commit()
                db.close()
                QMessageBox.information(self, "نجاح", "تم حذف الموظفين المحددين بنجاح")
                
                # تحديث الجدول (الحذف من الأسفل للأعلى للحفاظ علىIndexes)
                for row in sorted(rows_to_delete, reverse=True):
                    self.employeesTable.removeRow(row)
                    
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{str(e)}\nقد يكون الموظف مرتبطاً بقضايا أو مستندات حالية.")

    def select_all_employees(self, state):
        """تحديد أو إلغاء تحديد جميع الموظفين في الجدول"""
        is_checked = (state == Qt.Checked)
        for row in range(self.employeesTable.rowCount()):
            container = self.employeesTable.cellWidget(row, 0)
            if container:
                checkbox = container.layout().itemAt(0).widget()
                if checkbox:
                    checkbox.setChecked(is_checked)

    def add_row(self, user_id, username, password,full_name,email,phone,status,role_id):
        row_position = self.employeesTable.rowCount()
        self.employeesTable.insertRow(row_position)

        # Add checkbox in column 0
        checkbox = QCheckBox()
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.employeesTable.setCellWidget(row_position, 0, checkbox_container)
        checkbox_container.setProperty("user_id", user_id)

        # Add data items in columns 1-7
        items = [
            QTableWidgetItem(username),
            QTableWidgetItem(password),
            QTableWidgetItem(full_name),
            QTableWidgetItem(email),
            QTableWidgetItem(phone),
            QTableWidgetItem(status),
            QTableWidgetItem(role_id)
        ]
        for i, item in enumerate(items):
            item.setTextAlignment(Qt.AlignCenter)
            self.employeesTable.setItem(row_position, i + 1, item)

    def filter_table(self):
        search_text = self.searchBar.text().lower()
        for row in range(self.employeesTable.rowCount()):
            match = False
            for col in range(self.employeesTable.columnCount()):
                item = self.employeesTable.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.employeesTable.setRowHidden(row, not match)

    def log_out (self):
        if self.main_shell:
            self.main_shell.switch_to_login()
        else:
            self.close()


class AddUserWindow(QMainWindow):
    def __init__(self, admin_window, employee_data=None):
        super().__init__()
        self.admin = admin_window
        self.employee_data = employee_data  # إذا كان موجود = وضع التعديل
        self.is_edit_mode = employee_data is not None
        
        uic.loadUi("add_user.ui", self)  # افترض وجود الواجهة

        # جلب البيانات من جدول role
        self.db = DataBase()
        self.role_combo.clear()
        self.db.cur.execute("SELECT role_id, role_name FROM cms.role")
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

        # إذا كان وضع التعديل، املأ الحقول
        if self.is_edit_mode:
            self.setWindowTitle("تعديل بيانات الموظف")
            self.username_input.setText(employee_data['username'])
            self.password_input.setText(employee_data['password'])
            self.full_name_input.setText(employee_data['fullname'])
            self.email_input.setText(employee_data['email'])
            self.phone_input.setText(employee_data['phone'])
            
            # تحديد الحالة في combo
            status_index = self.status_combo.findText(employee_data['status'])
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)
            
            # تحديد الوظيفة في combo
            role_index = self.role_combo.findText(employee_data['role'])
            if role_index >= 0:
                self.role_combo.setCurrentIndex(role_index)

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
        role_name = self.role_combo.currentText()

        # إنشاء اتصال جديد بالقاعدة
        db = DataBase()

        if self.is_edit_mode:
            # وضع التعديل - تحديث البيانات
            db.cur.execute("""
                UPDATE cms.users 
                SET username = %s, password = %s, full_name = %s, email = %s, 
                    phone = %s, status = %s, role_id = %s
                WHERE user_id = %s
            """, (username, password, full_name, email, phone, status, role_id, self.employee_data['user_id']))
            db.conn.commit()
            db.close()

            # تحديث السطر في الجدول
            self.admin.update_table_row(
                self.employee_data['row'],
                username, password, full_name, email, phone, status, role_name
            )

            QMessageBox.information(self, "نجاح", "تم تحديث البيانات بنجاح")
        else:
            # وضع الإضافة - إدخال موظف جديد
            user_id = random.randint(20260000, 20269999)
            db.cur.execute(
                "INSERT INTO cms.users (user_id, username, password, full_name, email, phone, status, role_id) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (user_id, username, password, full_name, email, phone, status, role_id)
            )
            db.conn.commit()
            db.close()

            # تحديث جدول الموظفين في الواجهة الرئيسية
            self.admin.add_row(user_id, username, password, full_name, email, phone, status, role_name)

            QMessageBox.information(self, "نجاح", "تم إضافة المستخدم بنجاح")
        
        self.close()