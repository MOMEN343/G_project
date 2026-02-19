import os
from datetime import date
from db import DataBase
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt

class JudgeWindow(QMainWindow):
    def __init__(self, current_user_id, main_shell=None):
        super().__init__()
        self.current_user_id = current_user_id
        self.main_shell = main_shell
        self.db = DataBase()
        
        # Load the UI file
        uic.loadUi("judge.ui", self)
        
        # Connect Sidebar Buttons
        if hasattr(self, 'logoutBtn'):
            self.logoutBtn.clicked.connect(self.log_out)
        
        # Set active button style for the current page
        if hasattr(self, 'btn_calendar_side'):
            self.btn_calendar_side.setProperty("active", True)
        
        # Setup dynamic behavior
        self.load_judge_info()
        self.load_daily_sessions()

    def add_session_card(self, en_title, en_judge, en_room, en_time, ar_title, ar_judge, ar_room, ar_time):
        if not hasattr(self, 'scroll_layout'): return
        
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        
        # Timeline Part
        timeline = QWidget()
        timeline.setFixedWidth(40)
        t_lay = QVBoxLayout(timeline)
        t_lay.setContentsMargins(0, 0, 0, 0)
        line = QFrame()
        line.setFixedWidth(2)
        line.setStyleSheet("background-color: #ebe3d5;")
        dot = QFrame()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet("background-color: #b08d57; border-radius: 6px;")
        
        t_lay.addStretch()
        t_lay.addWidget(dot, 0, Qt.AlignCenter)
        t_lay.addWidget(line, 1, Qt.AlignCenter)
        t_lay.addStretch()
        
        row_layout.addWidget(timeline)
        
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #fcf6e8;
                border: 1px solid #ebe3d5;
                border-radius: 20px;
            }
        """)
        card.setFixedHeight(120)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # English Side
        left = QVBoxLayout()
        t_en = QLabel(en_title); t_en.setStyleSheet("color: #452829; font-weight: bold; font-size: 15px;")
        j_en = QLabel(f"Judge: {en_judge}"); j_en.setStyleSheet("color: #777; font-size: 13px;")
        r_en = QLabel(f"Room: {en_room}"); r_en.setStyleSheet("color: #777; font-size: 13px;")
        tm_en = QLabel(f"Time: {en_time}"); tm_en.setStyleSheet("color: #777; font-size: 13px;")
        left.addWidget(t_en); left.addWidget(j_en); left.addWidget(r_en); left.addWidget(tm_en)
        
        # Arabic Side
        right = QVBoxLayout()
        t_ar = QLabel(ar_title); t_ar.setStyleSheet("color: #452829; font-weight: bold; font-size: 15px;"); t_ar.setAlignment(Qt.AlignRight)
        j_ar = QLabel(f"القاضي: {ar_judge}"); j_ar.setStyleSheet("color: #777; font-size: 13px;"); j_ar.setAlignment(Qt.AlignRight)
        r_ar = QLabel(f"غرفة: {ar_room}"); r_ar.setStyleSheet("color: #777; font-size: 13px;"); r_ar.setAlignment(Qt.AlignRight)
        tm_ar = QLabel(f"الوقت: {ar_time}"); tm_ar.setStyleSheet("color: #777; font-size: 13px;"); tm_ar.setAlignment(Qt.AlignRight)
        right.addWidget(t_ar); right.addWidget(j_ar); right.addWidget(r_ar); right.addWidget(tm_ar)
        
        layout.addLayout(left)
        layout.addStretch()
        layout.addLayout(right)
        
        row_layout.addWidget(card)
        self.scroll_layout.addWidget(row_widget)



    def load_judge_info(self):
        self.db.cur.execute("SELECT full_name FROM cms.users WHERE user_id = %s", (self.current_user_id,))
        res = self.db.cur.fetchone()
        if res:
             name = res[0]
             if hasattr(self, 'judge_name_en'):
                self.judge_name_en.setText(f"Judge: Hon. {name}")
             if hasattr(self, 'judge_name_ar'):
                self.judge_name_ar.setText(f"القاضي: فضيلة الشيخ {name}")

    def load_daily_sessions(self):
        if not hasattr(self, 'scroll_layout'): return
        
        # Clear existing sessions
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        today = date.today().strftime("%Y-%m-%d")
        try:
            self.db.cur.execute("""
                SELECT s.session_time, s.session_date, c.case_number, c.case_type
                FROM cms.session s
                JOIN cms.court_case c ON s.case_id = c.case_id
                WHERE s.judge_id = %s AND s.session_date = %s
                ORDER BY s.session_time
            """, (self.current_user_id, today))
            
            sessions = self.db.cur.fetchall()
            for s in sessions:
                 time_str = s[0].strftime("%I:%M %p") if hasattr(s[0], 'strftime') else str(s[0])
                 room = "N/A" # Room table doesn't exist yet
                 case_info_en = f"Case {s[2]}: {s[3]}"
                 case_info_ar = f"القضية {s[2]}: {s[3]}"
                 self.add_session_card(case_info_en, "Hon. Judge", room, time_str,
                                       case_info_ar, "فضيلة القاضي", room, time_str)
            
            if not sessions:
                 lbl = QLabel("No sessions for today")
                 lbl.setAlignment(Qt.AlignCenter)
                 self.scroll_layout.addWidget(lbl)
        except Exception as e:
            print(f"Error loading sessions: {e}")

    def log_out (self):
        if self.main_shell:
            self.main_shell.switch_to_login()
        else:
            self.close()
