import os
import shutil
from docx import Document
from datetime import datetime, date, timedelta
from db import DataBase
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, 
    QGridLayout, QHBoxLayout, QCheckBox, QMessageBox, QMenu, 
    QWidgetAction, QFrame, QHeaderView
)
from PyQt5.QtGui import QColor, QFontDatabase
from PyQt5.QtCore import Qt, QPoint, QTimer, QTime

class UserWindow(QMainWindow):
    def __init__(self, current_user_id, main_shell=None):
        super().__init__()
        self.current_user_id = current_user_id
        self.main_shell = main_shell
        self.db = DataBase()

        # Load the new UI
        uic.loadUi("employee.ui", self)
        
        self.setStyleSheet("""
        * {
            font-family: "Alyamama", "Segoe UI Symbol";
            color: #452829;
        }
        QLineEdit {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
        }
        QLineEdit:focus {
            border: 1px solid #452829;
            background-color: #fcfcfc;
        }
        """)

        # Connect Buttons
        self.add_case.clicked.connect(self.new_case_dialog)
        self.docments.clicked.connect(self.show_documents)
        self.logoutBtn.clicked.connect(self.log_out)
        self.master_record.clicked.connect(self.show_master_record)
        self.btn_scheduling.clicked.connect(self.show_scheduling)
        self.btn_save_session.clicked.connect(self.save_session)
        self.case2.clicked.connect(self.show_calendar)
        self.searchMasterRecord.textChanged.connect(self.filter_master_record)
        self.searchScheduling.textChanged.connect(self.filter_scheduling)
        
        if hasattr(self, 'notification'):
            self.notification.clicked.connect(self.show_notifications)
            self.notification.setFocusPolicy(Qt.NoFocus)
        
        # --- Notification Badge ---
        if hasattr(self, 'notification') and hasattr(self, 'badge_label'):
            self.badge_label.setParent(self.notification)
            self.badge_label.move(24, 2)
            
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_badge)
            self.timer.start(5000)
            self.update_badge()

        # --- Deletion Feature UI Setup ---
        self.selected_documents = set()
        self.doc_checkboxes = [] 
        
        if hasattr(self, 'btn_delete_docs'):
            self.btn_delete_docs.clicked.connect(self.delete_selected_documents)
        if hasattr(self, 'check_all_docs'):
            self.check_all_docs.stateChanged.connect(self.select_all_documents)

        # Ensure we start at the empty page
        if hasattr(self, 'mainStack'):
             self.mainStack.setCurrentWidget(self.page_empty)
             
        if hasattr(self, 'files_grid'):
            self.files_grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 1. Clean up & Rebuild Calendar Page (The "Image 611" Ultimate Fix)
        # We handle this in code to ensure perfect alignment regardless of UI file state
        if hasattr(self, 'page_calendar') and hasattr(self, 'verticalLayout_calendar'):
            # Aggressively Hide everything that came from the UI file originally
            for w in self.page_calendar.findChildren(QWidget):
                if w.objectName() in ["calendarLeftPanel", "calendarHeader", "search_calendar", "btn_calendar_add", "label_calendar_date", "footerLayout"] or \
                   isinstance(w, (QPushButton, QtWidgets.QLineEdit, QLabel)) and w.parent() == self.page_calendar:
                    w.hide()
            
            # Reset layout to clear any spacers or odd items
            while self.verticalLayout_calendar.count():
                child = self.verticalLayout_calendar.takeAt(0)
                if child.widget(): child.widget().hide()

            # Set background for the calendar page
            self.page_calendar.setStyleSheet("QWidget#page_calendar { background-color: transparent; }")

            # Create Modern Header
            self.header_card = QWidget()
            self.header_card.setFixedHeight(85)
            h_layout = QHBoxLayout(self.header_card)
            h_layout.setContentsMargins(30, 20, 30, 10)
            
            # 1. Main Title
            title_lbl = QLabel("🗄 جدول القضاة")
            title_lbl.setStyleSheet("color: #452829; font-size: 20pt; font-weight: bold;")
            
            # 2. Date Navigator (Middle)
            self.date_nav_box = QWidget()
            d_layout = QHBoxLayout(self.date_nav_box)
            d_layout.setSpacing(15)
            btn_style = "QPushButton { color: #b08d57; font-size: 22px; border: none; background: transparent; font-weight: bold; } QPushButton:hover { color: #452829; }"
            
            self.custom_btn_prev = QPushButton("◀")
            self.custom_btn_prev.setStyleSheet(btn_style)
            self.custom_label_date = QLabel()
            self.custom_label_date.setStyleSheet("color: #452829; font-size: 19px; font-family: 'Alyamama';")
            self.custom_btn_next = QPushButton("▶")
            self.custom_btn_next.setStyleSheet(btn_style)
            
            d_layout.addWidget(self.custom_btn_next)
            d_layout.addWidget(self.custom_label_date)
            d_layout.addWidget(self.custom_btn_prev)

            self.custom_search = QtWidgets.QLineEdit()
            self.custom_search.setPlaceholderText("ابحث في الجدول... 🔍")
            self.custom_search.setFixedWidth(350)
            self.custom_search.setFixedHeight(45)
            self.custom_search.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 5px 15px;
                    font-size: 14px;
                    color: #452829;
                }
                QLineEdit:focus {
                    border: 2px solid #452829;
                }
            """)

            # Assemble Header Layout
            h_layout.addWidget(title_lbl)
            h_layout.addStretch()
            h_layout.addWidget(self.date_nav_box)
            h_layout.addStretch()
            h_layout.addWidget(self.custom_search)

            # Table Box
            self.table_box = QFrame()
            self.table_box.setStyleSheet("QFrame { background-color: #f6f4f2; border-radius: 20px; border: 1px solid #e0e0e0; }")
            shadow = QtWidgets.QGraphicsDropShadowEffect()
            shadow.setBlurRadius(25); shadow.setColor(QColor(0,0,0,15)); shadow.setOffset(0,5)
            self.table_box.setGraphicsEffect(shadow)
            
            t_layout = QVBoxLayout(self.table_box)
            t_layout.setContentsMargins(15, 15, 15, 15)
            
            if hasattr(self, 'mainCalendarTable'):
                self.mainCalendarTable.setParent(self.table_box)
                t_layout.addWidget(self.mainCalendarTable)
                self.mainCalendarTable.show()
                self.mainCalendarTable.setStyleSheet("""
                    QTableWidget { background-color: transparent; border: none; gridline-color: #f7f7f7; color: #452829; }
                    QHeaderView::section { background-color: #fcfcfc; color: #452829; font-weight: bold; padding: 15px; border: none; border-bottom: 2px solid #eeeeee; }
                """)
                self.mainCalendarTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            # Assemble
            self.verticalLayout_calendar.addWidget(self.header_card)
            self.verticalLayout_calendar.addWidget(self.table_box)
            self.verticalLayout_calendar.setStretch(1, 1)
            self.verticalLayout_calendar.setContentsMargins(20, 0, 20, 20)

            # Connections
            self.current_cal_date = date.today()
            self.custom_btn_prev.clicked.connect(lambda: self.show_calendar(self.current_cal_date - timedelta(days=1)))
            self.custom_btn_next.clicked.connect(lambda: self.show_calendar(self.current_cal_date + timedelta(days=1)))
            self.custom_search.textChanged.connect(self.filter_calendar_table)

        # Force initial state
        if hasattr(self, 'mainStack') and hasattr(self, 'page_empty'):
             self.mainStack.setCurrentWidget(self.page_empty)
        
        # Point global label to custom one for updates
        self.label_calendar_date = self.custom_label_date
        
        # Reset styles so no buttons are highlighted on start
        self.reset_sidebar_styles()

    def get_hijri_date_string(self, date):
        """
        Converts a Gregorian date to a Hijri date string using a robust iterative algorithm.
        Matches the Kuwaiti/Tabular Islamic calendar.
        """
        try:
            jd = date.toordinal() + 1721425 + 1
            days_since_hijra = jd - 1948440
            cycles = days_since_hijra // 10631
            rem_days = days_since_hijra % 10631
            leap_years = [2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29]
            year_in_cycle = 0
            while True:
                year_in_cycle += 1
                is_leap = year_in_cycle in leap_years
                days_in_this_year = 355 if is_leap else 354
                if rem_days < days_in_this_year:
                    break
                rem_days -= days_in_this_year
            h_year = cycles * 30 + year_in_cycle
            h_month = 0
            for m in range(1, 13):
                h_month = m
                days_in_this_month = 30 if m % 2 != 0 else 29
                if m == 12 and (year_in_cycle in leap_years):
                    days_in_this_month = 30
                if rem_days < days_in_this_month:
                    break
                rem_days -= days_in_this_month
            h_day = rem_days + 1
            m_names = ["", "محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة", 
                       "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]
            return f"{int(h_day)} {m_names[int(h_month)]} {int(h_year)} هـ"
        except Exception as e:
            print(f"Hijri Conversion Error: {e}")
            return "تاريخ غير متوفر"

    def update_badge(self):
        try:
            db = DataBase()
            db.cur.execute("""
                SELECT COUNT(*) FROM cms.notification 
                WHERE user_id = %s AND is_read = FALSE
            """, (self.current_user_id,))
            count = db.cur.fetchone()[0]
            db.close()

            if count > 0:
                self.badge_label.setText(str(count) if count < 10 else "9+")
                self.badge_label.show()
            else:
                self.badge_label.hide()
        except Exception as e:
            print(f"Error checking notifications: {e}")

    def show_notifications(self):
        db = DataBase()
        db.cur.execute("""
            SELECT notification_id, message, created_at, document_id 
            FROM cms.notification 
            WHERE user_id = %s AND is_read = FALSE
            ORDER BY created_at DESC
            LIMIT 10
        """, (self.current_user_id,))
        notifications = db.cur.fetchall()
        
        if notifications:
            ids = tuple([n[0] for n in notifications])
            if len(ids) == 1:
                db.cur.execute("UPDATE cms.notification SET is_read = TRUE WHERE notification_id = %s", (ids[0],))
            else:
                db.cur.execute("UPDATE cms.notification SET is_read = TRUE WHERE notification_id IN %s", (ids,))
            db.conn.commit()
        db.close()
        
        self.update_badge()

        menu = QMenu(self)
        menu.setMinimumWidth(350)
        menu.setStyleSheet("""
            QMenu {
                background-color: #452829;
                color: white;
                border: 1px solid #f3db93;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        if not notifications:
            action = QWidgetAction(menu)
            lbl = QLabel("لا توجد إشعارات جديدة")
            lbl.setStyleSheet("color: #f3e8df; padding: 10px;")
            lbl.setAlignment(Qt.AlignCenter)
            action.setDefaultWidget(lbl)
            menu.addAction(action)
        else:
            for notif_id, msg, created_at, doc_id in notifications:
                time_str = created_at.strftime("%I:%M %p")
                item_widget = QWidget()
                item_widget.setStyleSheet("background-color: transparent;")
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(10, 5, 10, 5)
                item_layout.setDirection(QHBoxLayout.RightToLeft)
                
                msg_label = QLabel(msg)
                msg_label.setStyleSheet("color: white; font-weight: bold; font-family: 'Alyamama'; font-size: 14px;")
                msg_label.setWordWrap(True)
                msg_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                time_label = QLabel(time_str)
                time_label.setStyleSheet("color: #f3db93; font-size: 12px;")
                time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                item_layout.addWidget(msg_label, 1)
                item_layout.addWidget(time_label, 0)
                
                action = QWidgetAction(menu)
                action.setDefaultWidget(item_widget)
                
                if doc_id:
                     action.triggered.connect(lambda checked, d=doc_id: self.handle_notification_click(d))
                
                menu.addAction(action)
                menu.addSeparator()

        menu.exec_(self.notification.mapToGlobal(QPoint(0, self.notification.height())))

    def handle_notification_click(self, document_id):
        self.show_documents(highlight_id=document_id)

    def reset_sidebar_styles(self):
        buttons = [self.add_case, self.docments, self.master_record, self.btn_scheduling, self.case2]
        for btn in buttons:
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def show_documents(self, highlight_id=None):
        self.reset_sidebar_styles()
        self.docments.setProperty("active", True)
        self.docments.style().unpolish(self.docments)
        self.docments.style().polish(self.docments)
        if hasattr(self, 'mainStack'):
            self.mainStack.setCurrentWidget(self.page_documents)

        try:
            db_clear = DataBase()
            db_clear.cur.execute("UPDATE cms.notification SET is_read = TRUE WHERE user_id = %s", (self.current_user_id,))
            db_clear.conn.commit()
            db_clear.close()
            self.update_badge()
        except Exception as e:
            print(f"Error clearing notifications: {e}")

        if hasattr(self, 'files_grid'):
            self.selected_documents.clear()
            self.doc_checkboxes.clear()
            if hasattr(self, 'check_all_docs'):
                self.check_all_docs.blockSignals(True)
                self.check_all_docs.setChecked(False)
                self.check_all_docs.blockSignals(False)
                
            while self.files_grid.count():
                item = self.files_grid.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        db = DataBase()
        db.cur.execute("""
            SELECT d.file_path, d.document_id, n.created_at
            FROM cms.file_transfer ft
            JOIN cms.document d ON ft.document_id = d.document_id
            LEFT JOIN cms.notification n ON d.document_id = n.document_id AND n.user_id = ft.receiver_id
            WHERE ft.receiver_id = %s
            ORDER BY ft.transfer_date DESC
        """, (self.current_user_id,))
        files = db.cur.fetchall()
        db.close()

        row_idx = 0
        for (file_path, doc_id, created_at) in files:
            row_widget = QWidget()
            row_widget.setFixedHeight(80)
            
            normal_style = """
                QWidget {
                    background-color: white;
                    border-bottom: 1px solid #e0e0e0;
                }
                QWidget:hover {
                    background-color: #f9f9f9;
                }
            """
            
            if highlight_id and doc_id == highlight_id:
                highlight_style = normal_style + "QWidget { background-color: #fff8e1; }"
                row_widget.setStyleSheet(highlight_style)
                QTimer.singleShot(3000, lambda w=row_widget: w.setStyleSheet(normal_style))
            else:
                row_widget.setStyleSheet(normal_style)

            layout = QHBoxLayout(row_widget)
            layout.setContentsMargins(20, 10, 20, 10)
            layout.setSpacing(15)

            checkbox = QCheckBox()
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")
            checkbox.setProperty("doc_id", doc_id)
            checkbox.stateChanged.connect(lambda state, d=doc_id: self.toggle_doc_selection(d, state))
            self.doc_checkboxes.append(checkbox)
            layout.addWidget(checkbox)
            
            icon = QLabel("📄")
            icon.setStyleSheet("font-size: 30px; background: transparent; border: none;")
            
            file_name = os.path.basename(file_path)
            name_label = QLabel(file_name)
            name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; background: transparent; border: none;")
            name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            time_str = created_at.strftime("%I:%M %p") if created_at else ""
            time_label = QLabel(time_str)
            time_label.setStyleSheet("color: #777; font-size: 14px; background: transparent; border: none; font-family: 'Alyamama';")
            time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            spacer = QWidget()
            spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            spacer.setStyleSheet("background: transparent; border: none;")

            btn_extract = QPushButton("استخراج إعلان الخصوم")
            btn_extract.setCursor(Qt.PointingHandCursor)
            btn_extract.setFocusPolicy(Qt.NoFocus)
            btn_extract.setMinimumHeight(40)
            btn_extract.setStyleSheet("""
                QPushButton {
                    background-color: #452829; 
                    color: white; 
                    border-radius: 5px; 
                    padding: 5px 15px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #f3db93;
                    color: black;
                }
            """)
            btn_extract.clicked.connect(lambda checked, d=doc_id: self.extract_notification_file(d))

            btn_open = QPushButton("فتح")
            btn_open.setCursor(Qt.PointingHandCursor)
            btn_open.setFocusPolicy(Qt.NoFocus)
            btn_open.setMinimumHeight(40)
            btn_open.setStyleSheet("""
                QPushButton {
                    background-color: #452829; 
                    color: white; 
                    border-radius: 5px; 
                    padding: 5px 20px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #f3db93;
                    color: black;
                }
            """)
            btn_open.clicked.connect(lambda checked, p=file_path: self.open_file(p))

            layout.addWidget(icon)
            layout.addWidget(name_label)
            layout.addWidget(time_label)
            layout.addWidget(spacer)
            layout.addWidget(btn_extract)
            layout.addWidget(btn_open)

            self.files_grid.addWidget(row_widget, row_idx, 0)
            row_idx += 1

    def toggle_doc_selection(self, doc_id, state):
        if state == Qt.Checked:
            self.selected_documents.add(doc_id)
        else:
            self.selected_documents.discard(doc_id)

    def select_all_documents(self, state):
        is_checked = (state == Qt.Checked)
        for cb in self.doc_checkboxes:
            cb.setChecked(is_checked)

    def delete_selected_documents(self):
        if not self.selected_documents:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار المستندات المراد حذفها أولاً.")
            return

        confirm = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف {len(self.selected_documents)} من المستندات المختارة؟\nهذا الإجراء سيحذف السجلات من النظام بشكل نهائي.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                db = DataBase()
                for doc_id in self.selected_documents:
                    db.cur.execute("DELETE FROM cms.notification WHERE document_id = %s", (doc_id,))
                    db.cur.execute("DELETE FROM cms.file_transfer WHERE document_id = %s", (doc_id,))
                    db.cur.execute("DELETE FROM cms.document WHERE document_id = %s", (doc_id,))
                db.conn.commit()
                db.close()
                QMessageBox.information(self, "نجاح", "تم حذف المستندات المختارة بنجاح.")
                self.show_documents()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{str(e)}")

    def extract_notification_file(self, doc_id):
        try:
            db = DataBase()
            db.cur.execute("""
                SELECT 
                    COALESCE(c1.plaintiff_name, c2.plaintiff_name) as plaintiff_name,
                    COALESCE(c1.plaintiff_address, c2.plaintiff_address) as plaintiff_address,
                    COALESCE(c1.defendant_name, c2.defendant_name) as defendant_name,
                    COALESCE(c1.defendant_address, c2.defendant_address) as defendant_address,
                    d.document_type
                FROM cms.document d
                LEFT JOIN cms.client c1 ON d.client_id = c1.client_id
                LEFT JOIN cms.case_client cc ON d.case_id = cc.case_id
                LEFT JOIN cms.client c2 ON cc.client_id = c2.client_id
                WHERE d.document_id = %s
            """, (doc_id,))
            result = db.cur.fetchone()
            db.close()
            
            if not result:
                QMessageBox.warning(self, "خطأ", "لم يتم العثور على بيانات الموكل للمستند المحدد")
                return
            
            plaintiff_name, plaintiff_address, defendant_name, defendant_address, doc_type = result
            if not plaintiff_name:
                QMessageBox.warning(self, "تنبيه", "بيانات الموكل (المدعي) ناقصة أو غير مرتبطة بشكل صحيح بهذا المستند.")
                return

            plaintiff_address = plaintiff_address if plaintiff_address else ""
            defendant_name = defendant_name if defendant_name else ""
            defendant_address = defendant_address if defendant_address else ""
            doc_type = doc_type if doc_type else "-"

            template_path = os.path.join("files", "إعلان خصوم.docx")
            if not os.path.exists(template_path):
                QMessageBox.warning(self, "خطأ", f"قالب إعلان الخصوم غير موجود:\n{template_path}")
                return
            
            safe_name = "".join([c for c in plaintiff_name if c.isalnum() or c in (' ', '_')]).rstrip()
            final_filename = f"إعلان خصوم - {safe_name}.docx"
            final_file_path = os.path.join("files", final_filename)
            shutil.copy2(template_path, final_file_path)
            
            doc = Document(final_file_path)
            
            p_addr = plaintiff_address if plaintiff_address else ""
            p_from = p_addr.split('-')[0].strip() if '-' in p_addr else p_addr
            p_res = p_addr.split('-')[1].strip() if '-' in p_addr else "-"

            d_addr = defendant_address if defendant_address else ""
            d_from = d_addr.split('-')[0].strip() if '-' in d_addr else d_addr
            d_res = d_addr.split('-')[1].strip() if '-' in d_addr else "-"

            placeholders = {
                "{PLAINTIFF_NAME}": plaintiff_name if plaintiff_name else "",
                "{PLAINTIFF_FROM}": p_from,
                "{PLAINTIFF_RESIDENT}": p_res,
                "{DEFENDANT_NAME}": defendant_name if defendant_name else "",
                "{DEFENDANT_FROM}": d_from,
                "{DEFENDANT_RESIDENT}": d_res,            
                "{CURRENT_CASE_TYPE}": doc_type if doc_type else "",
            }

            for key in placeholders:
                val = str(placeholders[key])
                if val and not val.startswith(" "):
                    placeholders[key] = " " + val
            
            def replace_in_doc(doc, placeholders):
                paragraphs = list(doc.paragraphs)
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            paragraphs.extend(list(cell.paragraphs))
                
                for p in paragraphs:
                    for key, val in placeholders.items():
                        if key in p.text:
                            key_found_in_run = False
                            for run in p.runs:
                                if key in run.text:
                                    run.text = run.text.replace(key, str(val))
                                    key_found_in_run = True
                            
                            if not key_found_in_run and key in p.text:
                                style_run = p.runs[0] if p.runs else None
                                bold, italic, f_name, f_size = None, None, None, None
                                if style_run:
                                    bold, italic = style_run.bold, style_run.italic
                                    f_name, f_size = style_run.font.name, style_run.font.size
                                new_text = p.text.replace(key, str(val))
                                for run in p.runs: run.text = ""
                                new_run = p.add_run(new_text)
                                if style_run:
                                    new_run.bold = bold
                                    new_run.italic = italic
                                    if f_name: new_run.font.name = f_name
                                    if f_size: new_run.font.size = f_size
            
            replace_in_doc(doc, placeholders)
            doc.save(final_file_path)
            QMessageBox.information(self, "نجاح", f"تم استخراج وتعديل إعلان الخصوم بنجاح!\n\nالملف: {final_filename}")
            
            try:
                os.startfile(final_file_path)
            except Exception as e:
                print(f"Could not open file: {e}")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء استخراج إعلان الخصوم:\n{str(e)}")
            
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
        if self.main_shell:
            self.main_shell.switch_to_login()
        else:
            self.close()

    def show_calendar(self, selected_qdate=None):
        db = DataBase()
        self.reset_sidebar_styles()
        self.case2.setProperty("active", True)
        self.case2.style().unpolish(self.case2)
        self.case2.style().polish(self.case2)
        
        self.mainStack.setCurrentWidget(self.page_calendar)
        
        # Determine the date to show
        if selected_qdate:
             if hasattr(selected_qdate, 'toPyDate'):
                 selected_date = selected_qdate.toPyDate()
             elif isinstance(selected_qdate, (date, datetime)):
                 selected_date = selected_qdate
             else:
                 selected_date = date.today()
        else:
             selected_date = date.today()

        # Update global state to keep buttons in sync
        self.current_cal_date = selected_date

        # Update Date Display
        hijri_str = self.get_hijri_date_string(selected_date)
        greg_str = selected_date.strftime("%d %B %Y")
        combined_date = f"{hijri_str}  |  {greg_str}"
        
        if hasattr(self, 'label_calendar_date'):
             self.label_calendar_date.setText(combined_date)
             self.label_calendar_date.setStyleSheet("color: #452829; font-size: 18px; font-family: 'Alyamama';")
        
        # Fetch Judges
        db.cur.execute("""
            SELECT user_id, full_name FROM cms.users WHERE role_id = 4 ORDER BY user_id
        """)
        judges_data = db.cur.fetchall()
        
        judge_names = ["ساعة"] + [f"القاضي {judge[1]} " for judge in judges_data]
        j_id = [(j[0],) for j in judges_data] 
        
        table = self.mainCalendarTable
        table.setColumnCount(len(judge_names))
        table.setHorizontalHeaderLabels(judge_names)
        
        # Hours from 08:00 to 16:00
        hours_list = [f"{h:02d}:00" for h in range(8, 17)]
        table.setRowCount(len(hours_list))
        table.verticalHeader().setVisible(False)
        
        # Style Header
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section { 
                background-color: #fcfcfc; 
                font-weight: bold; 
                border: 1px solid #e0e0e0; 
                color: #452829;
                padding: 10px;
                font-family: 'Alyamama';
            }
        """)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.clearContents()
        
        # Helper to add a high-end styled block
        def add_session_block(row, col, text, color_type="maroon"):
            colors = {
                "maroon": "#452829",
                "gold": "#b08d57", 
                "beige": "#ebe3d5"
            }
            text_colors = {
                "maroon": "white",
                "gold": "white",
                "beige": "#452829"
            }
            
            bg_color = colors.get(color_type, "#452829")
            fg_color = text_colors.get(color_type, "white")
            
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(4, 4, 4, 4)
            
            card = QFrame()
            card.setStyleSheet(f"background-color: {bg_color}; border-radius: 8px; border: none;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {fg_color}; font-weight: bold; font-family: 'Alyamama'; font-size: 11px; background: transparent; border: none;")
            
            card_layout.addWidget(lbl)
            container_layout.addWidget(card)
            table.setCellWidget(row, col, container)

        # Fill the Time Column
        for i, h in enumerate(hours_list):
            item = QtWidgets.QTableWidgetItem(h)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor("#452829"))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            table.setItem(i, 0, item)

        # --- REAL DATABASE SESSIONS ---
        today_str = selected_date.strftime("%Y-%m-%d")
        
        for i, (j_id_val,) in enumerate(j_id):
            db.cur.execute("""
                SELECT session_time, case_id
                FROM cms.session
                WHERE judge_id = %s AND session_date = %s
            """, (j_id_val, today_str))
            sessions = db.cur.fetchall()

            for s_time_val, case_id_val in sessions:
                # Fetch case details
                db.cur.execute("SELECT case_number, case_type FROM cms.court_case WHERE case_id = %s", (case_id_val,))
                case_res = db.cur.fetchone()
                if not case_res: continue
                    
                case_num, case_type = case_res
                
                # Format time "HH:00"
                if hasattr(s_time_val, 'strftime'):
                    t_str = s_time_val.strftime("%H:00")
                else:
                    t_str = str(s_time_val)[:2] + ":00"
                
                if t_str in hours_list:
                    row_idx = hours_list.index(t_str)
                    color_choice = ["maroon", "gold", "beige"][case_id_val % 3]
                    add_session_block(row_idx, i + 1, f"{case_type}\n{case_num}", color_choice)

        for i in range(len(hours_list)):
            table.setRowHeight(i, 70)
        db.close()

    def filter_calendar_table(self, text):
        """Filters the sessions inside the calendar table cells based on search text."""
        table = self.mainCalendarTable
        search_term = text.lower()
        
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                widget = table.cellWidget(row, col)
                if widget:
                    children = widget.findChildren(QLabel)
                    found = False
                    for child in children:
                        if search_term in child.text().lower():
                            found = True
                            break
                    
                    if not search_term:
                         widget.setHidden(False)
                    elif found:
                         widget.setHidden(False)
                    else:
                         widget.setHidden(True)

    def filter_master_record(self, text):
        table = self.masterRecordTable
        for row in range(table.rowCount()):
            match = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            table.setRowHidden(row, not match)

    def filter_scheduling(self, text):
        table = self.schedulingTable
        for row in range(table.rowCount()):
            match = False
            for col in range(1, table.columnCount()):
                item = table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            table.setRowHidden(row, not match)

    def show_master_record(self):
        self.reset_sidebar_styles()
        self.master_record.setProperty("active", True)
        self.master_record.style().unpolish(self.master_record)
        self.master_record.style().polish(self.master_record)
        
        db = DataBase()
        db.cur.execute("""
            SELECT ct.case_number, c.plaintiff_name,c.defendant_name, ct.case_type, ct.filing_date, ct.status
            FROM cms.case_client cc
            JOIN cms.client c ON cc.client_id = c.client_id
            JOIN cms.court_case ct ON cc.case_id = ct.case_id
            ORDER BY ct.filing_date DESC
        """)
        records = db.cur.fetchall()
        db.close()

        table = self.masterRecordTable
        table.verticalHeader().setVisible(False)
        table.setRowCount(0)
        table.setRowCount(len(records))
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        for row_idx, row_data in enumerate(records):
            for col_idx, value in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx, col_idx, item)
                
                if col_idx == 5: # Status column
                    if str(value) == "جديد":
                        item.setForeground(QColor("#2ECC71"))
                    elif str(value) == "مغلق":
                        item.setForeground(QColor("#E74C3C"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                table.setItem(row_idx, col_idx, item)

        self.searchMasterRecord.clear()
        self.mainStack.setCurrentWidget(self.page_master_record)

    def show_scheduling(self):
        self.reset_sidebar_styles()
        self.btn_scheduling.setProperty("active", True)
        self.btn_scheduling.style().unpolish(self.btn_scheduling)
        self.btn_scheduling.style().polish(self.btn_scheduling)
        self.mainStack.setCurrentWidget(self.page_scheduling)
        
        db = DataBase()
        db.cur.execute("""
            SELECT cc.case_id, c.plaintiff_name, c.defendant_name, ct.case_type
            FROM cms.case_client cc
            JOIN cms.client c ON cc.client_id = c.client_id
            JOIN cms.court_case ct ON cc.case_id = ct.case_id
            WHERE cc.case_id NOT IN (
                SELECT case_id FROM cms.session WHERE status = 'Scheduled'
            )
            ORDER BY ct.filing_date DESC
        """)
        records = db.cur.fetchall()
        db.close()
        
        self.searchScheduling.clear()
        table = self.schedulingTable
        table.setRowCount(0)
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(records))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.scheduling_checkboxes = [] 
        for row, data in enumerate(records):
            chk = QCheckBox()
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(chk)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            table.setCellWidget(row, 0, cell_widget)
            self.scheduling_checkboxes.append((chk, data[0]))
            
            for col, val in enumerate(data, start=1):
                item = QtWidgets.QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)

        self.judgeComboBox.clear()
        self.judgeComboBox.addItem("اختر القاضي")
        db = DataBase()
        db.cur.execute("SELECT user_id, full_name FROM cms.users WHERE role_id = 4")
        judges = db.cur.fetchall()
        db.close()
        for judge in judges:
            self.judgeComboBox.addItem(judge[1], judge[0])

        if hasattr(self, 'sessionTimeInput'):
            self.sessionTimeInput.setMinimumTime(QTime(8, 0))
            self.sessionTimeInput.setMaximumTime(QTime(14, 59))

    def save_session(self):
        selected_case_id = None
        if not hasattr(self, 'scheduling_checkboxes'): return

        for chk, case_id in self.scheduling_checkboxes:
            if chk.isChecked():
                selected_case_id = case_id
                break
        
        if not selected_case_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار قضية")
            return
            
        judge_id = self.judgeComboBox.currentData()
        if not judge_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار القاضي")
            return

        val_time = self.sessionTimeInput.time()
        if val_time.hour() < 8 or val_time.hour() > 14:
             QMessageBox.warning(self, "تنبيه", "وقت الجلسة يجب أن يكون بين 8 صباحاً و 2 ظهراً (14:00) ليظهر في الجدول بشكل صحيح.")
             return

        session_date = self.sessionDateInput.date().toString("yyyy-MM-dd")
        session_time = val_time.toString("HH:mm")
        
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        db = DataBase()
        try:
            db.cur.execute("""
                SELECT count(*) FROM cms.session 
                WHERE judge_id = %s AND session_date = %s AND session_time = %s AND status = 'Scheduled'
            """, (judge_id, session_date, session_time))
            if db.cur.fetchone()[0] > 0:
                QtWidgets.QApplication.restoreOverrideCursor()
                QMessageBox.warning(self, "تنبيه", "يوجد جلسة أخرى لهذا القاضي في نفس الموعد!")
                return

            db.cur.execute("""
                INSERT INTO cms.session (session_date, session_time, status, case_id, judge_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_date, session_time, 'Scheduled', selected_case_id, judge_id))
            db.conn.commit()

            db.cur.execute("SELECT case_number FROM cms.court_case WHERE case_id = %s", (selected_case_id,))
            case_number_val = db.cur.fetchone()[0]

            db.cur.execute("""
                SELECT file_path FROM cms.document
                WHERE case_id = %s ORDER BY upload_date DESC LIMIT 1
            """, (selected_case_id,))
            res = db.cur.fetchone()
            
            if res and os.path.exists(res[0]):
                doc = Document(res[0])
                placeholders = {          
                    "{CASE_NUMBER}": str(case_number_val),
                    "{SESSION_DATE}": session_date,
                    "{SESSION_TIME}": session_time
                }
                for p in doc.paragraphs:
                    for run in p.runs:
                        for key, val in placeholders.items():
                            if key in run.text: run.text = run.text.replace(key, str(val))
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for p in cell.paragraphs:
                                for run in p.runs:
                                    for key, val in placeholders.items():
                                        if key in run.text: run.text = run.text.replace(key, str(val))
                doc.save(res[0])

            QtWidgets.QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "نجاح", "تم حفظ الجلسة وتحديث ملف الدعوى بنجاح ✅")
            self.show_scheduling()
        except Exception as e:
             QtWidgets.QApplication.restoreOverrideCursor()
             QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {e}")
        finally:
            db.close()

    def new_case_dialog(self):
        db = DataBase()
        db.cur.execute("""
            SELECT client_id, plaintiff_name, defendant_name, case_type
            FROM cms.client
            WHERE client_id NOT IN (SELECT client_id FROM cms.case_client)
            """)
        clients = db.cur.fetchall()
        db.close()

        if not clients:
            QMessageBox.information(self, "تنبيه", "لا توجد عملاء في قاعدة البيانات بعد.")
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("إنشاء قضية جديدة")
        dialog.setFixedSize(550, 350)
        layout = QtWidgets.QVBoxLayout(dialog)
        dialog.setLayoutDirection(Qt.RightToLeft)

        layout.addWidget(QLabel("اختر القضايا:"))
        table = QtWidgets.QTableWidget()
        table.setRowCount(len(clients))
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["اختيار", "المدعي", "المدعى عليه", "نوع القضية"])
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        table.setLayoutDirection(Qt.RightToLeft)

        checkboxes = []
        for row, client in enumerate(clients):
            client_id, p_name, d_name, c_type = client
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            cb_layout = QHBoxLayout(checkbox_widget)
            cb_layout.addWidget(checkbox)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            table.setCellWidget(row, 0, checkbox_widget)
            checkboxes.append(checkbox)
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(p_name))
            table.setItem(row, 2, QtWidgets.QTableWidgetItem(d_name))
            table.setItem(row, 3, QtWidgets.QTableWidgetItem(c_type))

        layout.addWidget(table)
        save_btn = QPushButton("إنشاء القضايا")
        layout.addWidget(save_btn)

        def create_case():
            selected_rows = [i for i, cb in enumerate(checkboxes) if cb.isChecked()]
            if not selected_rows:
                QMessageBox.warning(dialog, "تنبيه", "اختر قضية واحدة على الأقل")
                return

            db = DataBase()
            for idx in selected_rows:
                client_id, p_name, d_name, c_type = clients[idx]
                db.cur.execute("SELECT count(*) FROM cms.court_case")
                case_count = db.cur.fetchone()[0]
                case_number = f"{datetime.now().strftime('%Y')}/{case_count + 1}"
                
                db.cur.execute("""
                    INSERT INTO cms.court_case (case_type, case_number, status, filing_date, year, description, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING case_id
                """, (c_type, case_number, "مفتوحة", datetime.now().date(), datetime.now().year, "-", self.current_user_id))
                new_case_id = db.cur.fetchone()[0]

                db.cur.execute("INSERT INTO cms.case_client (case_id, client_id, role_in_case) VALUES (%s, %s, %s)", (new_case_id, client_id, "Plaintiff"))
                db.cur.execute("UPDATE cms.document SET case_id = %s WHERE uploaded_by = %s AND case_id IS NULL AND document_type = %s", (new_case_id, self.current_user_id, c_type))

            db.conn.commit()
            db.close()
            QMessageBox.information(dialog, "نجاح", f"تم إنشاء {len(selected_rows)} قضية بنجاح ✅")
            dialog.accept()

        save_btn.clicked.connect(create_case)
        dialog.exec_()
