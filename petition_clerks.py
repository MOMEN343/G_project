import os
import shutil
import random
from datetime import date, datetime
from docx import Document
from db import DataBase
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, QTimer

class Petition_Clerks(QMainWindow):
    def __init__(self, current_user_id, main_shell=None):
        super().__init__()
        self.db = DataBase()
        self.c_u_i = current_user_id
        self.main_shell = main_shell
        self.current_case_type = None
        self.current_template = None

        uic.loadUi("petition_clerks2.ui", self)
        self.setStyleSheet("""
        * {
            font-family: "Alyamama";
            color: #452829;
        }
        """)
        
        self.sendFile.clicked.connect(self.process_full_workflow)
        self.logoutBtn.clicked.connect(self.log_out)
        self.sendFile.setFocusPolicy(Qt.NoFocus)
        self.logoutBtn.setFocusPolicy(Qt.NoFocus)
        
        self.case_config = {
            "case1": {"label": "نفقة زوجة", "template": "لائحة دعوى نفقة زوجة.docx"},
            "case2": {"label": "عفش بيت", "template": "لائحة دعوى عفش بيت.docx"}, 
            "case3": {"label": "مهر مؤجل", "template": "لائحة دعوى مهر مؤجل.docx"},
            "case4": {"label": "نفقة عفش غيابي", "template": "nafqa.docx"},
            "case5": {"label": "نفقة زوجة غيابي", "template": "nafqa.docx"},
            "case6": {"label": "نفقة صغار", "template": "nafqa.docx"},
        }

        for btn_id in self.case_config.keys():
            if hasattr(self, btn_id):
                btn = getattr(self, btn_id)
                btn.clicked.connect(self.handle_case_selection_click)
                btn.setFocusPolicy(Qt.NoFocus)

        self.load_receivers()

        if hasattr(self, 'employeesTable'):
             QTimer.singleShot(0, lambda: self.employeesTable.setFocus())

        self.setTabOrder(self.plaintiff_name, self.plaintiff_national_id)
        self.setTabOrder(self.plaintiff_national_id, self.plaintiff_phone)
        self.setTabOrder(self.plaintiff_phone, self.plaintiff_address)
        self.setTabOrder(self.plaintiff_address, self.defendant_name)
        self.setTabOrder(self.defendant_name, self.defendant_national_id)
        self.setTabOrder(self.defendant_national_id, self.defendant_phone)
        self.setTabOrder(self.defendant_phone, self.defendant_address)
        self.setTabOrder(self.defendant_address, self.comboBox)
        self.setTabOrder(self.comboBox, self.sendFile)

    def load_receivers(self):
        try:
            db = DataBase()
            db.cur.execute("SELECT user_id, full_name FROM cms.users WHERE role_id = '2'")
            users = db.cur.fetchall()
            self.comboBox.clear()
            self.comboBox.addItem("اختر الموظف المستلم...", None)
            for user_id, name in users:
                self.comboBox.addItem(name, user_id)
            db.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load receivers: {str(e)}")

    def handle_case_selection_click(self):
        btn = self.sender()
        if btn:
            btn_id = btn.objectName()
            if btn_id in self.case_config:
                config = self.case_config[btn_id]
                self.current_case_type = config["label"]
                self.current_template = config["template"]
                self.label_2.setText(f"أدخل بيانات لائحة دعوى {self.current_case_type}")

    def process_full_workflow(self):
        if not hasattr(self, 'current_case_type') or not self.current_case_type:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار نوع القضية أولاً من القائمة الجانبية.")
            return

        receiver_index = self.comboBox.currentIndex()
        if receiver_index <= 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار الموظف المستلم.")
            return
        receiver_id = self.comboBox.itemData(receiver_index)

        try:
            db = DataBase()
            db.cur.execute("""
                INSERT INTO cms.client (plaintiff_name, plaintiff_national_id, plaintiff_phone, plaintiff_address,
                                        defendant_name, defendant_national_id, defendant_phone, defendant_address, case_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING client_id
            """, (
                self.plaintiff_name.text(), self.plaintiff_national_id.text(), self.plaintiff_phone.text(),
                self.plaintiff_address.text(), self.defendant_name.text(), self.defendant_national_id.text(),
                self.defendant_phone.text(), self.defendant_address.text(), self.current_case_type 
            ))
            client_id = db.cur.fetchone()[0]
            db.conn.commit()
            db.close()
        except Exception as e:
             QMessageBox.warning(self, "Error", f"Failed to register client: {str(e)}")
             return

        try:
            template_path = os.path.join("files", self.current_template)
            if not os.path.exists(template_path):
                QMessageBox.warning(self, "Error", f"Template file not found: {template_path}")
                return

            safe_name = "".join([c for c in self.plaintiff_name.text() if c.isalnum() or c in (' ', '_')]).rstrip()
            final_filename = f"{self.current_case_type} - {safe_name}.docx"
            final_file = os.path.join("files", final_filename)
            shutil.copy2(template_path, final_file)
            doc = Document(final_file)

            days_map = {
                "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
                "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"
            }
            day_in_arabic = days_map.get(date.today().strftime("%A"), date.today().strftime("%A"))

            p_addr = self.plaintiff_address.text()
            p_from = p_addr.split('-')[0].strip() if '-' in p_addr else p_addr
            p_res = p_addr.split('-')[1].strip() if '-' in p_addr else "-"

            d_addr = self.defendant_address.text()
            d_from = d_addr.split('-')[0].strip() if '-' in d_addr else d_addr
            d_res = d_addr.split('-')[1].strip() if '-' in d_addr else "-"

            placeholders = {
                "{DATE_DAY}": day_in_arabic,
                "{DATE_FULL}": date.today().strftime("%d/%m/%Y"),
                "{PLAINTIFF_NAME}": self.plaintiff_name.text(),
                "{PLAINTIFF_FROM}": p_from,
                "{PLAINTIFF_RESIDENT}": p_res,
                "{DEFENDANT_NAME}": self.defendant_name.text(),
                "{DEFENDANT_FROM}": d_from,
                "{DEFENDANT_RESIDENT}": d_res,            
            }

            def replace_in_doc(doc, placeholders, p_from, p_res, d_from, d_res):
                import re
                paragraphs = list(doc.paragraphs)
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            paragraphs.extend(list(cell.paragraphs))
                
                for p in paragraphs:
                    full_text = p.text
                    updated = False
                    for key, val in placeholders.items():
                        if key in full_text:
                            full_text = full_text.replace(key, str(val))
                            updated = True
                    
                    is_plaintiff_line = re.search(r"المدع[ـ]*ية", full_text)
                    is_defendant_line = re.search(r"المدع[ـ]*ي[ـ]*[\s]*عليه|المدع[ـ]*ى[ـ]*[\s]*عليه", full_text)
                    
                    if is_plaintiff_line and not is_defendant_line:
                        if self.plaintiff_name.text() not in full_text:
                            full_text = re.sub(r"المدع[ـ]*ية\s*/?[ـ_\s]*", f"المدعية/ {self.plaintiff_name.text()} ", full_text)
                        if p_from not in full_text:
                            full_text = re.sub(r"من[ـ_\s]+", f"من {p_from} ", full_text)
                        if p_res not in full_text:
                            full_text = re.sub(r"وسكان[ـ_\s]+", f"وسكان {p_res} ", full_text)
                        updated = True
                    
                    if is_defendant_line:
                        if self.defendant_name.text() not in full_text:
                            full_text = re.sub(r"(المدع[ـ]*ي[ـ]*\s*عليه|المدع[ـ]*ى[ـ]*\s*عليه)\s*/?[ـ_\s]*", f"المدعى عليه/ {self.defendant_name.text()} ", full_text)
                        if d_from not in full_text:
                            full_text = re.sub(r"من[ـ_\s]+", f"من {d_from} ", full_text)
                        if d_res not in full_text:
                            full_text = re.sub(r"وسكان[ـ_\s]+", f"وسكان {d_res} ", full_text)
                        updated = True

                    if updated:
                        if len(p.runs) > 0:
                            p.runs[0].text = full_text
                            for i in range(1, len(p.runs)): p.runs[i].text = ""
                        else: p.add_run(full_text)

            replace_in_doc(doc, placeholders, p_from, p_res, d_from, d_res)
            doc.save(final_file)
            
            db = DataBase()
            db.cur.execute("""
                INSERT INTO cms.document (document_type, file_path, uploaded_by, client_id)
                VALUES (%s, %s, %s, %s)
                RETURNING document_id
            """, (self.current_case_type, final_file, self.c_u_i, client_id))
            doc_id = db.cur.fetchone()[0]
            db.conn.commit()
            db.close()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate file: {str(e)}")
            return

        try:
            db = DataBase()
            db.cur.execute("""
                INSERT INTO cms.file_transfer (transfer_id, transfer_date, status, document_id, sender_id, receiver_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (random.randint(1, 1000000), date.today(), "pending", doc_id, self.c_u_i, receiver_id))
            db.conn.commit()
            db.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to send file: {str(e)}")
            return

        try:
            notification_msg = f"({self.current_case_type} - \"{self.plaintiff_name.text().strip()}\" جديد)"
            db = DataBase()
            db.cur.execute("""
                INSERT INTO cms.notification (message, user_id, created_at, document_id)
                VALUES (%s, %s, NOW(), %s)
            """, (notification_msg, receiver_id, doc_id))
            db.conn.commit()
            db.close()
        except Exception as e:
            print(f"Failed to send notification: {e}")

        QMessageBox.information(self, "نجاح", f"تم تسجيل الموكل، إنشاء الملف وإرساله بنجاح!\n\nالمسار:\n{final_file}")
        
        self.plaintiff_name.clear()
        self.plaintiff_national_id.clear()
        self.plaintiff_phone.clear()
        self.plaintiff_address.clear()
        self.defendant_name.clear()
        self.defendant_national_id.clear()
        self.defendant_phone.clear()
        self.defendant_address.clear()
        self.comboBox.setCurrentIndex(0)
        self.label_2.setText("أدخل بيانات لائحة الدعوى:")

    def log_out (self):
        if self.main_shell:
            self.main_shell.switch_to_login()
        else:
            self.close()  
