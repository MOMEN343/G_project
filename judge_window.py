import os
import sys
from datetime import date, timedelta
from db import DataBase
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QSizePolicy, QTextEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QGridLayout,
    QInputDialog, QLineEdit, QDialog, QFormLayout, QDateEdit, QTimeEdit, QComboBox
)
from PyQt5.QtCore import Qt, QDate, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor

# ── Colour palette ────────────────────────────────────────────
CARD_COLORS = [
    {"bg": "#D6EEF0", "accent": "#3AAEBC", "text": "#1a6e78"},   # teal
    {"bg": "#FDF5DC", "accent": "#C9A227", "text": "#7a5e10"},   # gold
    {"bg": "#EDE8F8", "accent": "#8B6FD4", "text": "#4a3080"},   # purple
    {"bg": "#FFE8E8", "accent": "#C0524A", "text": "#7a2820"},   # red
    {"bg": "#E8F4E8", "accent": "#4A9E5C", "text": "#2a5e34"},   # green
    {"bg": "#FDE8D8", "accent": "#B06530", "text": "#6a3518"},   # orange
]

ARABIC_MONTHS = [
    "يناير","فبراير","مارس","أبريل","مايو","يونيو",
    "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"
]
ARABIC_DAYS = ["الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
ARABIC_NUMS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def to_arabic_num(n):
    return str(n).translate(ARABIC_NUMS)


def greg_to_hijri(d):
    # Simplified arithmetical Hijri conversion
    jd = d.toordinal() + 1721425
    l = jd - 1948440 + 10632
    n = int((l - 1) / 10631)
    l = l - 10631 * n + 354
    j = (int((10985 - l) / 5316)) * (int((50 * l) / 17719)) + (int(l / 5670)) * (int((43 * l) / 15238))
    l = l - (int((30 - j) / 15)) * (int((17719 * j) / 50)) - (int(j / 16)) * (int((15238 * j) / 43)) + 29
    m = int((24 * l) / 709)
    d_h = l - int((709 * m) / 24)
    y_h = 30 * n + j - 30
    return f"{y_h}/{m}/{d_h}"


class JudgeWindow(QMainWindow):
    def __init__(self, current_user_id, main_shell=None):
        super().__init__()
        self.current_user_id = current_user_id
        self.main_shell = main_shell
        self.db = DataBase()

        self._current_date = date.today()
        self._cal_month = QDate(self._current_date.year, self._current_date.month, 1)
        # store session info per day for calendar cells
        self._session_dates: set[date] = set()   # dates that have sessions
        self._session_map: dict[date, list] = {}
        self.current_verdict_case_id = None
        self.current_verdict_case_number = None
        self.current_verdict_session_id = None
        

        uic.loadUi("judge.ui", self)



        # Judge icon → white
        if hasattr(self, 'headerIcon'):
            pixmap = QPixmap("icons/Judge.png")
            wp = QPixmap(pixmap.size())
            wp.fill(Qt.transparent)
            p = QPainter(wp)
            p.drawPixmap(0, 0, pixmap)
            p.setCompositionMode(QPainter.CompositionMode_SourceIn)
            p.fillRect(wp.rect(), Qt.white)
            p.end()
            self.headerIcon.setPixmap(wp.scaledToWidth(50, Qt.SmoothTransformation))

        # Notification Badge & Click
        if hasattr(self, 'notification'):
            self.notification.clicked.connect(self.on_notification_clicked)
            self.notification.setFocusPolicy(Qt.NoFocus)

        if hasattr(self, 'notification') and hasattr(self, 'badge_label'):
            self.badge_label.setParent(self.notification)
            self.badge_label.move(24, 2)
            
            from PyQt5.QtCore import QTimer
            self.badge_timer = QTimer(self)
            self.badge_timer.timeout.connect(self.update_badge)
            self.badge_timer.start(5000)

        self.update_badge()

        # Sidebar buttons
        if hasattr(self, 'logoutBtn'):
            self.logoutBtn.clicked.connect(self.log_out)
        if hasattr(self, 'btn_calendar_side'):
            self.btn_calendar_side.clicked.connect(self.on_calendar_clicked)
        if hasattr(self, 'btn_scale'):
            self.btn_scale.clicked.connect(self.on_cases_clicked)
        if hasattr(self, 'btn_book'):
            self.btn_book.clicked.connect(self.on_decisions_clicked)
        if hasattr(self, 'btn_gear'):
            self.btn_gear.clicked.connect(self.on_settings_clicked)

        # Day nav buttons
        if hasattr(self, 'btn_day_prev'):
            self.btn_day_prev.clicked.connect(self._prev_day)
        if hasattr(self, 'btn_day_next'):
            self.btn_day_next.clicked.connect(self._next_day)
        if hasattr(self, 'scroll_layout'):
            self.scroll_layout.setAlignment(Qt.AlignTop)
        # Month nav buttons
        if hasattr(self, 'btn_cal_prev'):
            self.btn_cal_prev.clicked.connect(self._prev_month)
        if hasattr(self, 'btn_cal_next'):
            self.btn_cal_next.clicked.connect(self._next_month)

        self.load_judge_info()
        self._load_all_session_dates()

        # ensure calendar headers are correct even if UI had duplicates or got lost
        self._setup_day_headers()

        self._rebuild_calendar()
        self._load_day_sessions()
        self.set_active_button(self.btn_calendar_side)

    # ── Sidebar helpers ───────────────────────────────────────
    def reset_sidebar_styles(self):
        for btn in [self.btn_calendar_side, self.btn_scale, self.btn_book, self.btn_gear]:
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_active_button(self, button):
        self.reset_sidebar_styles()
        button.setProperty("active", True)
        button.style().unpolish(button)
        button.style().polish(button)

    def on_calendar_clicked(self):  
        self.set_active_button(self.btn_calendar_side)
        self._show_calendar_page()
    def on_cases_clicked(self):
        self.set_active_button(self.btn_scale)
        self.show_my_cases_page()
    def on_decisions_clicked(self):
        self.set_active_button(self.btn_book)
        self.show_verdicts_page()
    def on_settings_clicked(self):  self.set_active_button(self.btn_gear)

    # ── Judge info ────────────────────────────────────────────
    def load_judge_info(self):
        try:
            self.db.cur.execute(
                "SELECT full_name FROM cms.users WHERE user_id = %s",
                (self.current_user_id,)
            )
            res = self.db.cur.fetchone()
            if res:
                name = res[0]
                # update calendar judge name too
                if hasattr(self, 'calJudgeName'):
                    self.calJudgeName.setText(name)
        except Exception as e:
            print(f"load_judge_info error: {e}")

    # ── Notifications ─────────────────────────────────────────
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
                if hasattr(self, 'badge_label'):
                    self.badge_label.setText(str(count) if count < 10 else "9+")
                    self.badge_label.show()
            else:
                if hasattr(self, 'badge_label'):
                    self.badge_label.hide()
        except Exception as e:
            print(f"update_badge error: {e}")

    def on_notification_clicked(self):
        from PyQt5.QtWidgets import QMenu, QWidgetAction
        from PyQt5.QtCore import QPoint
        
        menu = QMenu(self)
        menu.setFixedWidth(400)
        menu.setStyleSheet("""
            QMenu {
                background-color: #452829;
                border: 1px solid #b08d57;
                border-radius: 12px;
                padding: 10px;
                direction: rtl;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255,255,255,0.1);
                margin: 5px 0px;
            }
        """)

        try:
            db = DataBase()
            db.cur.execute("""
                SELECT message, created_at 
                FROM cms.notification 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (self.current_user_id,))
            notifs = db.cur.fetchall()
            
            # Delete after viewing
            db.cur.execute("DELETE FROM cms.notification WHERE user_id = %s", (self.current_user_id,))
            db.conn.commit()
            db.close()
            
            if not notifs:
                empty_action = menu.addAction("لا توجد إشعارات حالياً")
                empty_action.setEnabled(False)
            else:
                for msg, t in notifs:
                    item_widget = QWidget()
                    item_layout = QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(15, 10, 15, 10)
                    item_layout.setSpacing(10)
                    
                    time_str = t.strftime("%I:%M %p")
                    
                    msg_label = QLabel(msg)
                    msg_label.setStyleSheet("color: white; font-weight: bold; font-family: 'Alyamama'; font-size: 14px;")
                    msg_label.setWordWrap(True)
                    msg_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    time_label = QLabel(time_str)
                    time_label.setStyleSheet("color: #b08d57; font-size: 12px;")
                    time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    
                    sep = QLabel("|")
                    sep.setStyleSheet("color: rgba(255,255,255,0.2); font-weight: bold; font-size: 14px;")
                    
                    item_layout.addWidget(msg_label, 1)
                    item_layout.addWidget(sep, 0)
                    item_layout.addWidget(time_label, 0)
                    
                    action = QWidgetAction(menu)
                    action.setDefaultWidget(item_widget)
                    menu.addAction(action)
                    menu.addSeparator()

            self.update_badge()
            
            # Show the menu under the notification button
            pos = self.notification.mapToGlobal(QPoint(0, self.notification.height()))
            menu.exec_(pos)

        except Exception as e:
            print(f"show_notifications_menu error: {e}")

    # ── Session dates (for calendar dots) ────────────────────
    def _load_all_session_dates(self):
        """Populate both the set of active dates and a detailed map.
        The map stores plaintiff/defendant/type so calendar cells can show
        coloured rectangles with case info.

        The original schema stores clients separately from cases, so we
        join through the case_client table and pull names by role.
        """
        self._session_dates.clear()
        self._session_map.clear()
        try:
            # simpler query: join through case_client if exists then pull both names
            self.db.cur.execute("""
                SELECT
                    s.session_date,
                    cl.plaintiff_name,
                    cl.defendant_name,
                    c.case_type
                FROM cms.session s
                JOIN cms.court_case c ON s.case_id = c.case_id
                LEFT JOIN cms.case_client cc ON cc.case_id = c.case_id
                LEFT JOIN cms.client cl ON cc.client_id = cl.client_id
                WHERE s.judge_id = %s AND (s.status IS NULL OR s.status = 'Scheduled')
            """, (self.current_user_id,))
            rows = self.db.cur.fetchall()
            for session_date, plaintiff, defendant, case_type in rows:
                self._session_dates.add(session_date)
                info = {
                    'plaintiff': plaintiff or '',
                    'defendant': defendant or '',
                    'case_type': case_type or ''
                }
                self._session_map.setdefault(session_date, []).append(info)
        except Exception as e:
            print(f"_load_all_session_dates error: {e}")

    # ── Calendar rendering ────────────────────────────────────
    def _rebuild_calendar(self):
        if not hasattr(self, 'calGridLayout'):
            return

        # make sure headers remain in case layout was reset elsewhere
        self._setup_day_headers()

        # Update month label
        m = self._cal_month
        self.calMonthLabel.setText(
            f"{ARABIC_MONTHS[m.month()-1]} {to_arabic_num(m.year())}"
        )

        # Clear old grid
        layout = self.calGridLayout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        first_day = QDate(m.year(), m.month(), 1)
        days_in_month = m.daysInMonth()
        # Qt dayOfWeek: 1=Mon…7=Sun  →  col: Mon=0 … Sun=6
        dow_map = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}
        start_col = dow_map[first_day.dayOfWeek()]

        today_qdate = QDate.currentDate()
        sel_qdate = QDate(
            self._current_date.year,
            self._current_date.month,
            self._current_date.day
        )

        day = 1
        for row in range(6):
            if day > days_in_month:
                break
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(0)

            for col in range(7):
                if row == 0 and col < start_col:
                    # Empty placeholder
                    placeholder = QWidget()
                    placeholder.setFixedSize(32, 40)
                    row_layout.addWidget(placeholder)
                    continue
                if day > days_in_month:
                    placeholder = QWidget()
                    placeholder.setFixedSize(32, 40)
                    row_layout.addWidget(placeholder)
                    continue

                cell_date = QDate(m.year(), m.month(), day)
                py_date = date(m.year(), m.month(), day)
                has_session = py_date in self._session_dates

                cell = QWidget()
                # make the cell taller to accommodate session rectangles above the day
                cell.setFixedSize(34, 72)
                cell_vbox = QVBoxLayout(cell)
                cell_vbox.setContentsMargins(1, 1, 1, 1)
                cell_vbox.setSpacing(1)
                cell_vbox.setAlignment(Qt.AlignTop)

                # Only show dot indicator; remove detailed rectangles
                sessions = self._session_map.get(py_date, [])
                # do nothing with sessions here (dot below will indicate presence)

                # Day number button
                btn = QPushButton(to_arabic_num(day))
                btn.setFixedSize(32, 32)
                btn.setCursor(Qt.PointingHandCursor)

                if cell_date == sel_qdate:
                    btn.setObjectName("calDayBtnSelected")
                elif cell_date == today_qdate:
                    btn.setObjectName("calDayBtnToday")
                else:
                    btn.setObjectName("calDayBtn")

                btn.setStyleSheet(self.calendarPanel.styleSheet())
                # Capture day for lambda
                _d = py_date
                btn.clicked.connect(lambda _, d=_d: self._on_cal_day_clicked(d))
                cell_vbox.addWidget(btn, 0, Qt.AlignCenter)

                # Session dot (kept as fallback indicator)
                dot_label = QLabel()
                dot_label.setFixedSize(6, 6)
                if has_session:
                    dot_label.setStyleSheet(
                        "background-color: #b08d57; border-radius: 3px;"
                    )
                else:
                    dot_label.setStyleSheet("background: transparent;")
                cell_vbox.addWidget(dot_label, 0, Qt.AlignCenter)

                # push everything to the top of the cell
                cell_vbox.addStretch()

                row_layout.addWidget(cell)
                day += 1

            layout.addWidget(row_widget)

    def _on_cal_day_clicked(self, d: date):
        self._current_date = d
        self._cal_month = QDate(d.year, d.month, 1)
        self._rebuild_calendar()
        self._load_day_sessions()

    def _setup_day_headers(self):
        """Populate and style the seven weekday header labels.
        The UI originally used identical objectNames which can confuse
        Qt's loader; this method safely finds the labels via the layout
        and ensures the correct Arabic abbreviations are shown."""
        headers = ["اثنين", "ثلاثاء", "أربعاء", "خميس", "جمعة", "سبت", "أحد"]
        if not hasattr(self, 'dayHeadersLayout'):
            return
        for i in range(self.dayHeadersLayout.count()):
            item = self.dayHeadersLayout.itemAt(i)
            if item and item.widget():
                lbl = item.widget()
                lbl.setText(headers[i])
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("color: #b08d57; font-size: 11px; font-weight: bold; min-width: 32px; max-width: 32px; background: transparent;")
                lbl.setVisible(True)

    def _prev_month(self):
        self._cal_month = self._cal_month.addMonths(-1)
        self._rebuild_calendar()

    def _next_month(self):
        self._cal_month = self._cal_month.addMonths(1)
        self._rebuild_calendar()

    # ── Day navigation ────────────────────────────────────────
    def _prev_day(self):
        self._current_date -= timedelta(days=1)
        self._cal_month = QDate(self._current_date.year, self._current_date.month, 1)
        self._rebuild_calendar()
        self._load_day_sessions()

    def _next_day(self):
        self._current_date += timedelta(days=1)
        self._cal_month = QDate(self._current_date.year, self._current_date.month, 1)
        self._rebuild_calendar()
        self._load_day_sessions()

    def _update_date_label(self):
        """Update the main date display label in the sessions column."""
        d = self._current_date
        # Python weekday: 0=Mon...6=Sun. Mapping to ARABIC_DAYS (0=Mon...6=Sun)
        dow_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
        day_name = ARABIC_DAYS[dow_map[d.weekday()]]
        
        text = f"{day_name}، {to_arabic_num(d.day)} {ARABIC_MONTHS[d.month-1]} {to_arabic_num(d.year)}"
        if hasattr(self, 'currentDateLabel'):
            self.currentDateLabel.setText(text)

    # ── Session cards ─────────────────────────────────────────
    def _load_day_sessions(self):
        if not hasattr(self, 'scroll_layout'):
            return

        # refresh cached dates in case something changed externally
        self._load_all_session_dates()
        # ensure scroll layout alignment remains at top after clearing
        if hasattr(self, 'scroll_layout'):
            self.scroll_layout.setAlignment(Qt.AlignTop)
            # add a slightly larger gap above the very first card
            self.scroll_layout.addSpacing(16)

        # Clear
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._update_date_label()

        date_str = self._current_date.strftime("%Y-%m-%d")
        try:
            # query simplified to read names directly from client table
            self.db.cur.execute("""
                SELECT
                    s.session_time,
                    c.case_id,
                    c.case_number,
                    c.case_type,
                    cl.plaintiff_name,
                    cl.defendant_name,
                    s.session_id
                FROM cms.session s
                JOIN cms.court_case c ON s.case_id = c.case_id
                LEFT JOIN cms.case_client cc ON cc.case_id = c.case_id
                LEFT JOIN cms.client cl ON cc.client_id = cl.client_id
                WHERE s.judge_id = %s AND s.session_date = %s AND (s.status IS NULL OR s.status = 'Scheduled')
                ORDER BY s.session_time
            """, (self.current_user_id, date_str))

            sessions = self.db.cur.fetchall()

            if hasattr(self, 'sessionCountLabel'):
                self.sessionCountLabel.setText(
                    f"{to_arabic_num(len(sessions))} جلسة" if len(sessions) != 1
                    else "جلسة واحدة"
                )

            for idx, s in enumerate(sessions):
                time_str  = s[0].strftime("%I:%M %p") if hasattr(s[0], 'strftime') else str(s[0])
                case_id   = s[1]
                case_num  = s[2] or "—"
                case_type = s[3] or "—"
                plaintiff = s[4] or "غير محدد"
                defendant = s[5] or "غير محدد"
                session_id = s[6]
                color = CARD_COLORS[idx % len(CARD_COLORS)]
                self._add_session_card(time_str, case_id, case_num, case_type, plaintiff, defendant, color, session_id)

            if not sessions:
                self._show_empty_state()

        except Exception as e:
            print(f"_load_day_sessions error: {e}")
            self._show_empty_state()

    def _add_session_card(self, time_str, case_id, case_num, case_type, plaintiff, defendant, color, session_id):
        """Beautiful session card with plaintiff, defendant, case type."""
        card = QFrame()
        card.setObjectName("sessionCardOuter")
        card.setStyleSheet(f"""
            QFrame#sessionCardOuter {{
                background-color: {color['bg']};
                border-radius: 18px;
                border-left: 6px solid {color['accent']};
            }}
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(110)

        outer = QHBoxLayout(card)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(16)

        # ── Left: time block ──────────────────────────────────
        time_block = QFrame()
        time_block.setFixedWidth(80)
        time_block.setStyleSheet(f"""
            background-color: {color['accent']};
            border-radius: 12px;
        """)
        time_vbox = QVBoxLayout(time_block)
        time_vbox.setContentsMargins(4, 8, 4, 8)
        time_vbox.setSpacing(0)

        time_lbl = QLabel(time_str)
        time_lbl.setAlignment(Qt.AlignCenter)
        time_lbl.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold; background: transparent;"
        )
        time_vbox.addWidget(time_lbl)
        outer.addWidget(time_block)

        # ── Center: main info ─────────────────────────────────
        info = QVBoxLayout()
        info.setSpacing(6)

        # Case type + number
        type_row = QHBoxLayout()
        type_badge = QLabel(case_type)
        type_badge.setStyleSheet(f"""
            background-color: {color['accent']};
            color: white;
            border-radius: 8px;
            padding: 2px 10px;
            font-size: 12px;
            font-weight: bold;
        """)
        type_badge.setAlignment(Qt.AlignCenter)
        case_num_lbl = QLabel(f"رقم القضية: {case_num}")
        case_num_lbl.setStyleSheet(
            f"color: {color['text']}; font-size: 12px; background: transparent;"
        )
        type_row.addWidget(case_num_lbl)
        type_row.addStretch()
        type_row.addWidget(type_badge)
        info.addLayout(type_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {color['accent']}; max-height: 1px; opacity: 0.3;")
        info.addWidget(sep)

        # Plaintiff row
        plaintiff_row = QHBoxLayout()
        plaintiff_row.setSpacing(6)
        plaintiff_icon = QLabel("👤")
        plaintiff_icon.setStyleSheet("background: transparent; font-size: 13px;")
        plaintiff_role = QLabel("المدعي:")
        plaintiff_role.setStyleSheet(
            f"color: {color['text']}; font-size: 12px; background: transparent;"
        )
        plaintiff_name = QLabel(plaintiff)
        plaintiff_name.setStyleSheet(
            f"color: {color['text']}; font-size: 14px; font-weight: bold; background: transparent;"
        )
        plaintiff_row.addStretch()
        plaintiff_row.addWidget(plaintiff_name)
        plaintiff_row.addWidget(plaintiff_role)
        plaintiff_row.addWidget(plaintiff_icon)
        info.addLayout(plaintiff_row)

        # Defendant row
        defendant_row = QHBoxLayout()
        defendant_row.setSpacing(6)
        defendant_icon = QLabel("👤")
        defendant_icon.setStyleSheet("background: transparent; font-size: 13px; color: #888;")
        defendant_role = QLabel("المدعى عليه:")
        defendant_role.setStyleSheet(
            f"color: {color['text']}; font-size: 12px; background: transparent;"
        )
        defendant_name = QLabel(defendant)
        defendant_name.setStyleSheet(
            f"color: {color['text']}; font-size: 14px; font-weight: bold; background: transparent;"
        )
        defendant_row.addStretch()
        defendant_row.addWidget(defendant_name)
        defendant_row.addWidget(defendant_role)
        defendant_row.addWidget(defendant_icon)
        info.addLayout(defendant_row)

        outer.addLayout(info, stretch=1)

        self.scroll_layout.addWidget(card)
        # make card clickable to open verdicts page and add hover effect
        card.case_id = case_id
        card.case_num = case_num
        card.session_id = session_id
        card._original_stylesheet = card.styleSheet()
        card._color = color
        card.mouseReleaseEvent = lambda event: self._open_verdicts_page(card.case_id, card.case_num, card.session_id)
        card.enterEvent = lambda event: self._card_hover_enter(card)
        card.leaveEvent = lambda event: self._card_hover_leave(card)

    def _lighten_color(self, hex_color, factor=0.1):
        """Lighten a hex color by a factor (0.0 to 1.0)."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _card_hover_enter(self, card):
        """Add subtle hover effect on mouse enter."""
        color = card._color
        lightened_bg = self._lighten_color(color['bg'], 0.15)
        card.setStyleSheet(f"""
            QFrame#sessionCardOuter {{
                background-color: {lightened_bg};
                border-radius: 18px;
                border-left: 6px solid {color['accent']};
            }}
        """)

    def _card_hover_leave(self, card):
        """Remove hover effect on mouse leave."""
        color = card._color
        card.setStyleSheet(f"""
            QFrame#sessionCardOuter {{
                background-color: {color['bg']};
                border-radius: 18px;
                border-left: 6px solid {color['accent']};
            }}
        """)

    def _show_empty_state(self):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel("📋")
        icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)

        msg = QLabel("لا توجد جلسات في هذا اليوم")
        msg.setObjectName("empty_state_msg")
        msg.setAlignment(Qt.AlignCenter)

        vbox.addStretch()
        vbox.addWidget(icon_lbl)
        vbox.addSpacing(10)
        vbox.addWidget(msg)
        vbox.addStretch()

        self.scroll_layout.addWidget(container)



    def _open_verdicts_page(self, case_id, case_number, session_id):
        """Open verdicts page for this case and activate sidebar button."""
        self.set_active_button(self.btn_book)
        self.current_verdict_case_id = case_id
        self.current_verdict_case_number = case_number
        self.current_verdict_session_id = session_id
        self.show_verdicts_page()

    def _hide_calendar_controls(self):
        """Hide calendar header, date navigation, and calendar panel."""
        # Hide date nav layout (with buttons, date label, session count)
        if hasattr(self, 'dateNavLayout'):
            for i in range(self.dateNavLayout.count()):
                widget = self.dateNavLayout.itemAt(i).widget()
                if widget:
                    widget.hide()
        
        # Hide divider line below date nav
        if hasattr(self, 'headerDivider'):
            self.headerDivider.hide()
        
        # Hide calendar panel
        if hasattr(self, 'calendarPanel'):
            self.calendarPanel.hide()

    def _show_calendar_controls(self):
        """Show calendar header, date navigation, and calendar panel."""
        # Show date nav layout
        if hasattr(self, 'dateNavLayout'):
            for i in range(self.dateNavLayout.count()):
                widget = self.dateNavLayout.itemAt(i).widget()
                if widget:
                    widget.show()
        
        # Show divider line
        if hasattr(self, 'headerDivider'):
            self.headerDivider.show()
        
        # Show calendar panel
        if hasattr(self, 'calendarPanel'):
            self.calendarPanel.show()

    def _show_calendar_page(self):
        """Show calendar page."""
        self._show_calendar_controls()
        # Clear and reload calendar
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.scroll_layout.addSpacing(16)
        self._load_day_sessions()
        self._rebuild_calendar() # Refresh the grid (with dots) too!

    def show_verdicts_page(self):
        """Display verdicts page - show empty state or verdict form."""
        self._hide_calendar_controls()
        
        if not hasattr(self, 'current_verdict_case_id') or self.current_verdict_case_id is None:
            self._show_verdicts_empty_state()
            return

        case_id = self.current_verdict_case_id
        case_num = self.current_verdict_case_number

        # Clear scroll layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(8) # Reduced from 15
        vbox.setContentsMargins(20, 5, 20, 20) # Reduced top margin

        # Header with Back button
        header_layout = QHBoxLayout()
        header_layout.setDirection(QHBoxLayout.RightToLeft)
        
        header_title = QLabel(f"القرارات والأحكام - {case_num}")
        header_title.setObjectName("past_docs_header")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        back_btn = QPushButton("↩️ العودة للتقويم")
        back_btn.setObjectName("back_btn")
        # Direct styling with hover state 
        back_btn.setStyleSheet("""
            QPushButton#back_btn {
                background-color: #452829; 
                color: white; 
                border-radius: 8px; 
                padding: 8px 15px; 
                font-weight: bold; 
                border: 1px solid #b08d57;
            }
            QPushButton#back_btn:hover {
                background-color: #b08d57;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._back_to_calendar)
        header_layout.addWidget(back_btn)
        
        vbox.addLayout(header_layout)

        # Client Details section (PROMOTED TO TOP)
        try:
            db = DataBase()
            db.cur.execute("""
                SELECT 
                    plaintiff_name, plaintiff_national_id, plaintiff_phone, plaintiff_address,
                    defendant_name, defendant_national_id, defendant_phone, defendant_address
                FROM cms.client cl
                JOIN cms.case_client cc ON cl.client_id = cc.client_id
                WHERE cc.case_id = %s
                LIMIT 1
            """, (case_id,))
            client_data = db.cur.fetchone()
            db.close()

            if client_data:
                p_name, p_id, p_phone, p_addr, d_name, d_id, d_phone, d_addr = [str(x) if x else "—" for x in client_data]
                
                details_label = QLabel("بيانات أطراف الدعوى:")
                details_label.setObjectName("docs_label")
                vbox.addWidget(details_label)

                client_card = QFrame()
                client_card.setObjectName("client_card")
                card_vbox = QVBoxLayout(client_card)
                card_vbox.setContentsMargins(0, 0, 0, 0)
                card_vbox.setSpacing(0)

                table = QTableWidget(4, 2)
                table.setObjectName("client_table")
                table.setFocusPolicy(Qt.NoFocus)
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                table.setSelectionMode(QAbstractItemView.NoSelection)
                table.setHorizontalHeaderLabels(["المدعى عليه", "المدعي"])
                table.setLayoutDirection(Qt.RightToLeft)
                
                headers = ["الاسم الكامل", "رقم الهوية", "رقم الجوال", "العنوان"]
                table.setVerticalHeaderLabels(headers)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                table.setFixedHeight(220) 

                # Fill data
                data_map = [
                    (p_name, d_name),
                    (p_id, d_id),
                    (p_phone, d_phone),
                    (p_addr, d_addr)
                ]
                
                for r, (p_val, d_val) in enumerate(data_map):
                    table.setItem(r, 1, QTableWidgetItem(p_val))
                    table.setItem(r, 0, QTableWidgetItem(d_val))
                    for c in range(2):
                        item = table.item(r, c)
                        if item: 
                            item.setTextAlignment(Qt.AlignCenter)
                            # Add some padding logic via spaces or let style handle it
                            # But keep it compact

                card_vbox.addWidget(table)
                vbox.addWidget(client_card)
            else:
                error_card = QFrame()
                error_card.setObjectName("error_card")
                error_lay = QHBoxLayout(error_card)
                error_lay.setDirection(QHBoxLayout.RightToLeft)
                error_msg = QLabel("⚠️ لم يتم العثور على بيانات أطراف الدعوى المسجلة لهذه القضية.")
                error_msg.setObjectName("error_msg")
                error_lay.addWidget(error_msg)
                vbox.addWidget(error_card)
        except Exception as e:
            print(f"Client Table Error: {e}")
            err_label = QLabel(f"Error: {str(e)}")
            err_label.setStyleSheet("color: red;")
            vbox.addWidget(err_label)

        # Documents section
        docs_label = QLabel("المستندات السابقة:")
        docs_label.setObjectName("docs_label")
        vbox.addWidget(docs_label)

        docs_layout = QVBoxLayout()
        docs_layout.setSpacing(8)

        try:
            db = DataBase()
            db.cur.execute("""
                SELECT d.document_id, d.document_type, d.file_path
                FROM cms.document d
                WHERE d.case_id = %s
                ORDER BY d.upload_date DESC
            """, (case_id,))

            docs = db.cur.fetchall()
            db.close()

            for doc_id, doc_type, file_path in docs:
                file_card = QFrame()
                
                # Determine colors based on document type for a nicer visual hierarchy
                bg_color = "#fcf9f2"
                border_color = "#d6c7b5"
                accent_color = "#b08d57"
                icon_char = "📄"
                
                if "حكم" in doc_type:
                    bg_color = "#f0fdf4"
                    accent_color = "#4A9E5C"
                    icon_char = "⚖️"
                elif "لائحة" in doc_type or "إعلان" in doc_type:
                    bg_color = "#f0f7fd"
                    accent_color = "#3AAEBC"
                    icon_char = "📋" if "لائحة" in doc_type else "📢"

                file_card.setStyleSheet(f"""
                    QFrame {{
                        background: {bg_color};
                        border-radius: 12px;
                        border: 1px solid {border_color};
                        border-right: 6px solid {accent_color};
                    }}
                    QFrame:hover {{
                        background: #fdfdfd;
                        border-color: {accent_color};
                    }}
                """)
                file_card.setMinimumHeight(80)

                h = QHBoxLayout(file_card)
                h.setContentsMargins(16, 12, 16, 12)
                h.setSpacing(16)
                h.setDirection(QHBoxLayout.RightToLeft)

                # Icon
                icon = QLabel(icon_char)
                icon.setStyleSheet("font-size: 28px; background: transparent; border: none;")
                icon.setFixedWidth(40)
                icon.setAlignment(Qt.AlignCenter)
                h.addWidget(icon)

                # Info
                info = QVBoxLayout()
                info.setSpacing(4)
                
                title_lbl = QLabel(doc_type)
                title_lbl.setStyleSheet(f"font-size:15px; font-weight:bold; color:#452829; background: transparent; border: none;")
                info.addWidget(title_lbl)

                import os
                filename_only = os.path.basename(file_path)
                path_lbl = QLabel(filename_only)
                path_lbl.setStyleSheet("font-size:12px; color:#666; background: transparent; border: none;")
                info.addWidget(path_lbl)

                h.addLayout(info, stretch=1)

                # Open button
                open_btn = QPushButton("عرض المستند")
                open_btn.setCursor(Qt.PointingHandCursor)
                open_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {accent_color};
                        color: white;
                        font-weight: bold;
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-size: 13px;
                        border: none;
                    }}
                    QPushButton:hover {{ 
                        background: #452829; 
                    }}
                """)
                open_btn.clicked.connect(lambda chk, fp=file_path: self._open_document(fp))
                h.addWidget(open_btn)

                docs_layout.addWidget(file_card)

            if docs:
                docs_frame = QFrame()
                docs_frame.setStyleSheet("background: transparent; border: none;")
                docs_frame.setLayout(docs_layout)
                vbox.addWidget(docs_frame)
            else:
                no_docs = QLabel("لا توجد مستندات سابقة لهذه القضية")
                no_docs.setStyleSheet("color:#888; font-size:14px; font-style: italic; padding: 20px;")
                no_docs.setAlignment(Qt.AlignCenter)
                vbox.addWidget(no_docs)

        except Exception as e:
            print(f"Error loading documents: {e}")
            no_docs = QLabel("حدث خطأ أثناء تحميل المستندات")
            no_docs.setStyleSheet("color:#888;font-size:12px;")
            vbox.addWidget(no_docs)

        verdict_label = QLabel("أدخل مقدار النفقة")
        verdict_label.setObjectName("verdict_label")
        vbox.addWidget(verdict_label)

        self.verdict_text_edit = QTextEdit()
        self.verdict_text_edit.setPlaceholderText(" مقدار النفقة")
        self.verdict_text_edit.setMinimumHeight(150)
        self.verdict_text_edit.setMaximumHeight(250)
        self.verdict_text_edit.setStyleSheet("background-color: white !important; color: #452829; border: 1px solid #ddd; border-radius: 6px; font-size: 16px")
        vbox.addWidget(self.verdict_text_edit, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("حفظ و إنشاء ملف الحكم")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A9E5C; 
                color: white; 
                padding: 8px 16px; 
                border-radius: 8px; 
                font-size: 14px; 
                border: none;
            }
            QPushButton:hover {
                background-color: #3c7f4a;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_verdict)
        btn_layout.addWidget(save_btn)

        # Postpone Button
        postpone_btn = QPushButton("تأجيل الجلسة")
        postpone_btn.setStyleSheet("""
            QPushButton {
                background-color: #C0524A; 
                color: white; 
                padding: 8px 16px; 
                border-radius: 8px; 
                font-size: 14px; 
                border: none;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #a0423a;
            }
        """)
        postpone_btn.setCursor(Qt.PointingHandCursor)
        postpone_btn.clicked.connect(self._postpone_session)
        btn_layout.addWidget(postpone_btn)

        vbox.addLayout(btn_layout)

        self.scroll_layout.addWidget(container)

    def _postpone_session(self):
        """Handle session postponement with scheduling a future date and conflict check."""
        if not self.current_verdict_session_id or not self.current_verdict_case_id:
            QMessageBox.warning(self, "تنبيه", "لا توجد جلسة محددة لتأجيلها.")
            return

        # Premium Styled Dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("تأجيل الجلسة - موعد جديد")
        dialog.setFixedWidth(450)
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f3f0ea;
                border-radius: 15px;
            }
            QLabel {
                font-family: 'Alyamama';
                font-size: 14px;
                color: #452829;
                font-weight: bold;
            }
            QDateEdit, QTimeEdit {
                background-color: white;
                border: 1px solid #d6c7b5;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                min-height: 25px;
            }
            QPushButton#confirm_btn {
                background-color: #4A9E5C;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-family: 'Alyamama';
            }
            QPushButton#confirm_btn:hover { background-color: #3c7f4a; }
            QPushButton#cancel_btn {
                background-color: #C0524A;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                font-family: 'Alyamama';
            }
            QPushButton#cancel_btn:hover { background-color: #a0423a; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title_lbl = QLabel("📅 تحديد موعد التأجيل الجديد")
        title_lbl.setStyleSheet("font-size: 18px; color: #452829; text-align: center;")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        form = QFormLayout()
        form.setSpacing(15)
        
        date_input = QDateEdit(QDate.currentDate().addDays(7))
        date_input.setCalendarPopup(True)
        date_input.setMinimumDate(QDate.currentDate().addDays(1)) # Prevent same day or past
        
        from PyQt5.QtCore import QTime
        time_input = QTimeEdit(QTime(9, 0))
        time_input.setDisplayFormat("hh:mm AP")

        form.addRow("تاريخ الجلسة القادمة:", date_input)
        form.addRow("وقت الجلسة القادمة:", time_input)
        layout.addLayout(form)

        # Buttons
        buttons = QHBoxLayout()
        confirm_btn = QPushButton("تأكيد الموعد")
        confirm_btn.setObjectName("confirm_btn")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        
        buttons.addWidget(confirm_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        confirm_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            new_date = date_input.date().toPyDate()
            new_time = time_input.time().toPyTime()

            # ── Weekend Check (Friday=4, Saturday=5) ──
            if new_date.weekday() in [4, 5]:
                 QMessageBox.warning(self, "تنبيه", "لا يمكن جدولة جلسات في أيام الإجازة (الجمعة والسبت).")
                 return

            try:
                db = DataBase()
                # ── Conflict Check ──
                db.cur.execute("""
                    SELECT count(*) FROM cms.session 
                    WHERE judge_id = %s AND session_date = %s AND session_time = %s AND status = 'Scheduled'
                """, (self.current_user_id, new_date, new_time))
                
                conflict_count = db.cur.fetchone()[0]
                
                if conflict_count > 0:
                    QMessageBox.warning(self, "تعارض في المواعيد", "لا يمكنك تأجيل الجلسة لهذا الموعد، لديك جلسة أخرى مسجلة بالفعل في هذا الوقت.")
                    db.close()
                    return

                # 1. Update current session
                db.cur.execute("""
                    UPDATE cms.session 
                    SET status = 'Postponed'
                    WHERE session_id = %s
                """, (self.current_verdict_session_id,))
                
                # 2. Insert new session for the future
                db.cur.execute("""
                    INSERT INTO cms.session (session_date, session_time, status, case_id, judge_id, notes)
                    VALUES (%s, %s, 'Scheduled', %s, %s, %s)
                """, (new_date, new_time, self.current_verdict_case_id, self.current_user_id, "تأجيل من جلسة سابقة"))
                
                db.conn.commit()
                db.close()
                
                QMessageBox.information(self, "نجاح", f"تم تأجيل الجلسة بنجاح إلى تاريخ {new_date}")
                self._back_to_calendar()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في تأجيل الجلسة: {str(e)}")

    def show_my_cases_page(self, search_text=""):
        """Display 'My Cases' page with stats and searchable table."""
        self._hide_calendar_controls()
        
        # Clear scroll layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(15)
        vbox.setContentsMargins(20, 10, 20, 20)

        # Header Title
        title_lbl = QLabel("📖  القضايا الخاصة بي")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #452829; border-bottom: 2px solid #b08d57; padding-bottom: 5px;")
        vbox.addWidget(title_lbl)

        # --- Search Bar Section ---
        search_box = QFrame()
        search_box.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #d6c7b5;")
        search_lay = QHBoxLayout(search_box)
        search_lay.setContentsMargins(15, 8, 15, 8)
        search_lay.setDirection(QHBoxLayout.RightToLeft)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("border: none; font-size: 16px;")
        self.cases_search_input = QLineEdit()
        self.cases_search_input.setPlaceholderText("ابحث برقم القضية أو اسم الخصم...")
        self.cases_search_input.setText(search_text)
        self.cases_search_input.setStyleSheet("border: none; background: transparent; font-size: 15px;")
        self.cases_search_input.textChanged.connect(self._on_cases_search_changed)
        
        search_lay.addWidget(search_icon)
        search_lay.addWidget(self.cases_search_input)
        vbox.addWidget(search_box)

        # --- Statistics Cards ---
        try:
            db = DataBase()
            # Get total, active, and finished cases for THIS judge
            db.cur.execute("""
                SELECT count(DISTINCT c.case_id) FROM cms.court_case c
                JOIN cms.session s ON c.case_id = s.case_id
                WHERE s.judge_id = %s
            """, (self.current_user_id,))
            total_cnt = db.cur.fetchone()[0]

            db.cur.execute("""
                SELECT count(DISTINCT c.case_id) FROM cms.court_case c
                JOIN cms.session s ON c.case_id = s.case_id
                WHERE s.judge_id = %s AND c.status = 'مفتوحة'
            """, (self.current_user_id,))
            active_cnt = db.cur.fetchone()[0]
            
            finished_cnt = total_cnt - active_cnt
            db.close()
        except:
            total_cnt, active_cnt, finished_cnt = 0, 0, 0

        stats_lay = QHBoxLayout()
        stats_lay.setSpacing(20)

        def create_stat_card(label, count, color):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: white; 
                    border-radius: 15px; 
                    border: 1px solid #eee; 
                    border-right: 8px solid {color};
                }}
            """)
            card_lay = QVBoxLayout(card)
            card_lay.setSpacing(5)
            card_lay.setAlignment(Qt.AlignCenter)
            
            c_lbl = QLabel(to_arabic_num(count))
            c_lbl.setFixedSize(45, 45)
            c_lbl.setAlignment(Qt.AlignCenter)
            c_lbl.setStyleSheet(f"""
                QLabel {{
                    font-size: 20px; 
                    font-weight: bold; 
                    color: white; 
                    background-color: {color}; 
                    border-radius: 22px;
                    border: none;
                }}
            """)
            
            l_container = QWidget()
            l_container.setStyleSheet("background: transparent; border: none;")
            l_lay = QHBoxLayout(l_container)
            l_lay.setContentsMargins(0, 0, 0, 0)
            l_lay.setSpacing(8)
            l_lay.setAlignment(Qt.AlignCenter)
            
            l_lbl = QLabel(label)
            l_lbl.setStyleSheet("font-size: 15px; color: #555; font-weight: bold; border: none;")
            
            # Small vertical accent line to the right of text
            accent = QFrame()
            accent.setFixedSize(3, 14)
            accent.setStyleSheet(f"background-color: {color}; border-radius: 1px; border: none;")
            
            l_lay.addWidget(l_lbl)
            l_lay.addWidget(accent) # Accent on the right for RTL feel
            
            card_lay.addWidget(c_lbl, 0, Qt.AlignCenter)
            card_lay.addWidget(l_container, 0, Qt.AlignCenter)
            return card

        stats_lay.addWidget(create_stat_card("إجمالي القضايا", total_cnt, "#452829"))
        stats_lay.addWidget(create_stat_card("قضايا مفتوحة", active_cnt, "#3AAEBC"))
        stats_lay.addWidget(create_stat_card("قضايا منتهية", finished_cnt, "#4A9E5C"))
        vbox.addLayout(stats_lay)

        # --- Cases Table ---
        self.my_cases_table = QTableWidget()
        self.my_cases_table.setColumnCount(7)
        # Reversed order: Case Number on the right (first visual column in RTL)
        self.my_cases_table.setHorizontalHeaderLabels([
             "رقم القضية", "نوع القضية", "المدعي", "المدعى عليه", "الحالة", "تاريخ آخر جلسة", "الإجراء"
        ])
        self.my_cases_table.setLayoutDirection(Qt.RightToLeft)
        self.my_cases_table.verticalHeader().setVisible(False)
        self.my_cases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.my_cases_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.my_cases_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.my_cases_table.setObjectName("client_table") # Use existing table styles

        # Fetch case data
        try:
            db = DataBase()
            query = """
                SELECT DISTINCT ON (c.case_id)
                    c.case_id,
                    c.case_number,
                    c.case_type,
                    cl.plaintiff_name,
                    cl.defendant_name,
                    c.status,
                    (SELECT max(session_date) FROM cms.session WHERE case_id = c.case_id) as last_date
                FROM cms.court_case c
                JOIN cms.session s ON c.case_id = s.case_id
                LEFT JOIN cms.case_client cc ON c.case_id = cc.case_id
                LEFT JOIN cms.client cl ON cc.client_id = cl.client_id
                WHERE s.judge_id = %s
            """
            params = [self.current_user_id]
            if search_text:
                query += " AND (c.case_number ILIKE %s OR cl.plaintiff_name ILIKE %s OR cl.defendant_name ILIKE %s)"
                term = f"%{search_text}%"
                params.extend([term, term, term])
            
            query += " ORDER BY c.case_id, last_date DESC"
            db.cur.execute(query, tuple(params))
            rows = db.cur.fetchall()
            db.close()

            self.my_cases_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                # (case_id, case_num, case_type, plaintiff, defendant, status, last_date)
                self.my_cases_table.setRowHeight(i, 60)
                
                # Column 0: Case Num
                item_num = QTableWidgetItem(str(r[1]))
                item_num.setTextAlignment(Qt.AlignCenter)
                self.my_cases_table.setItem(i, 0, item_num)

                # Column 1: Case Type
                item_type = QTableWidgetItem(str(r[2] or "—"))
                item_type.setTextAlignment(Qt.AlignCenter)
                self.my_cases_table.setItem(i, 1, item_type)

                # Column 2: Plaintiff
                item_p = QTableWidgetItem(str(r[3] or "—"))
                item_p.setTextAlignment(Qt.AlignCenter)
                self.my_cases_table.setItem(i, 2, item_p)

                # Column 3: Defendant
                item_d = QTableWidgetItem(str(r[4] or "—"))
                item_d.setTextAlignment(Qt.AlignCenter)
                self.my_cases_table.setItem(i, 3, item_d)

                # Column 4: Status
                item_status = QTableWidgetItem(str(r[5] or "—"))
                item_status.setTextAlignment(Qt.AlignCenter)
                if r[5] == 'مفتوحة': item_status.setForeground(QColor("#3AAEBC"))
                else: item_status.setForeground(QColor("#4A9E5C"))
                self.my_cases_table.setItem(i, 4, item_status)

                # Column 5: Date
                item_date = QTableWidgetItem(str(r[6] or "—"))
                item_date.setTextAlignment(Qt.AlignCenter)
                self.my_cases_table.setItem(i, 5, item_date)

                # Column 6: Action Button
                btn_widget = QWidget()
                btn_lay = QHBoxLayout(btn_widget)
                btn_lay.setContentsMargins(10, 5, 10, 5)
                btn_lay.setAlignment(Qt.AlignCenter)
                
                view_btn = QPushButton("عرض القضية")
                view_btn.setFixedSize(110, 32)
                view_btn.setCursor(Qt.PointingHandCursor)
                view_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #452829; color: white; border-radius: 6px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #b08d57; }
                """)
                view_btn.clicked.connect(lambda _, cid=r[0], cnum=r[1]: self._open_verdicts_page(cid, cnum, None))
                btn_lay.addWidget(view_btn)
                self.my_cases_table.setCellWidget(i, 6, btn_widget)

        except Exception as e:
            print(f"My Cases Error: {e}")

        vbox.addWidget(self.my_cases_table)
        self.scroll_layout.addWidget(container)

    def _on_cases_search_changed(self):
        text = self.cases_search_input.text()
        self.show_my_cases_page(text)
        # Refocus search because page reload clears it
        self.cases_search_input.setFocus()
        self.cases_search_input.setCursorPosition(len(text))

    def _show_verdicts_empty_state(self):
        """Show guidance when verdicts page is opened without selecting a case."""

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setContentsMargins(40, 40, 40, 40)

        icon_lbl = QLabel("📋")
        icon_lbl.setStyleSheet("font-size: 64px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)

        msg1 = QLabel("اختر قضية من التقويم")
        msg1.setStyleSheet("color: #452829; font-size: 20px; font-weight: bold; background: transparent;")
        msg1.setAlignment(Qt.AlignCenter)

        msg2 = QLabel("توجه فوق والضغط على أحد المستطيلات لتحديد القضية وإدخال الحكم")
        msg2.setStyleSheet("color: #999; font-size: 14px; background: transparent; line-height: 1.5;")
        msg2.setAlignment(Qt.AlignCenter)
        msg2.setWordWrap(True)
        msg2.setMaximumWidth(500)

        vbox.addStretch()
        vbox.addWidget(icon_lbl)
        vbox.addSpacing(20)
        vbox.addWidget(msg1)
        vbox.addSpacing(10)
        vbox.addWidget(msg2)
        vbox.addStretch()

        self.scroll_layout.addWidget(container)

    def _open_document(self, file_path):
        """Open document file."""
        if os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"لم يتم فتح الملف: {e}")
        else:
            QMessageBox.warning(self, "خطأ", f"الملف غير موجود: {file_path}")

    def _save_verdict(self):
        """Save verdict using automated template selection based on case type."""
        case_id = self.current_verdict_case_id
        case_number = self.current_verdict_case_number
        if not case_id: return

        full_text = self.verdict_text_edit.toPlainText().strip()
        if not full_text:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال نص الحكم.")
            return

        # Simple logic: first line is amount, rest is verdict text
        lines = full_text.split('\n')
        amount = lines[0].strip()
        verdict_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else full_text

        try:
            from docx import Document
            from datetime import date
            import shutil
            import re

            db = DataBase()
            # 1. Fetch case details and CASE TYPE
            db.cur.execute("""
                SELECT cl.plaintiff_name, cl.defendant_name, cl.client_id, c.case_type, cl.plaintiff_address, cl.defendant_address
                FROM cms.court_case c
                JOIN cms.case_client cc ON c.case_id = cc.case_id
                JOIN cms.client cl ON cc.client_id = cl.client_id
                WHERE c.case_id = %s LIMIT 1
            """, (case_id,))
            res = db.cur.fetchone()
            if not res:
                QMessageBox.warning(self, "خطأ", "بيانات القضية غير مكتملة.")
                db.close()
                return
            p_full, d_full, client_id, case_type, p_addr, d_addr = res

            # Auto-template mapping
            if case_type == "نفقة زوجة":
                template_name = "ضبط دعوى نفقة زوجة"
            else:
                template_name = f"حكم - {case_type}"
            
            template_path = os.path.join("Template files", f"{template_name}.docx")
            
            # Fallback path logic
            if not os.path.exists(template_path) and case_type != "نفقة زوجة":
                template_path = os.path.join("Template files", f"الحكم - {case_type}.docx")

            if not os.path.exists(template_path):
                 QMessageBox.warning(self, "خطأ", f"لم يتم العثور على قالب لهذا النوع من القضايا: {case_type}\nتأكد من وجود ملف باسم '{template_name}.docx' في مجلد القوالب.")
                 db.close()
                 return

            # 2. Clerk Name
            db.cur.execute("""
                SELECT u.full_name FROM cms.users u
                JOIN cms.document d ON u.user_id = d.uploaded_by
                WHERE d.case_id = %s OR d.client_id = %s
                ORDER BY d.upload_date ASC LIMIT 1
            """, (case_id, client_id))
            cl_res = db.cur.fetchone()
            clerk_name = cl_res[0] if cl_res else "—"

            # 3. Process Document
            fname = f"{template_name}_{case_number.replace('/', '_')}_{date.today().isoformat()}.docx"
            final_path = os.path.join(os.getcwd(), "files", fname)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            shutil.copy2(template_path, final_path)
            
            doc = Document(final_path)
            p_parts = p_full.split() if p_full else []
            p_first = p_parts[0] if len(p_parts) > 0 else "—"
            p_second = p_parts[1] if len(p_parts) > 1 else ""
            p_third_fourth = " ".join(p_parts[2:]) if len(p_parts) > 2 else ""
            
            d_parts = d_full.split() if d_full else []
            d_first = d_parts[0] if len(d_parts) > 0 else "—"
            d_second = d_parts[1] if len(d_parts) > 1 else ""
            d_third_fourth = " ".join(d_parts[2:]) if len(d_parts) > 2 else ""
            
            p_addr_str = str(p_addr) if p_addr else ""
            p_from = p_addr_str.split('-')[0].strip() if '-' in p_addr_str else p_addr_str
            p_res = p_addr_str.split('-')[1].strip() if '-' in p_addr_str else "-"

            d_addr_str = str(d_addr) if d_addr else ""
            d_from = d_addr_str.split('-')[0].strip() if '-' in d_addr_str else d_addr_str
            d_res = d_addr_str.split('-')[1].strip() if '-' in d_addr_str else "-"

            judge_name = self.calJudgeName.text() if hasattr(self, 'calJudgeName') else "—"
            
            placeholders = {
                "{PLAINTIFF_NAME}": p_full,
                "{DEFENDANT_NAME}": d_full,
                "{PLAINTIFF_FULL}": p_full, 
                "{DEFENDANT_FULL}": d_full,
                "{PLAINTIFF_FIRST}": p_first, 
                "{PLAINTIFF_SECOND}": p_second,
                "{PLAINTIFF_THIRD_FOURTH}": p_third_fourth,
                "{DEFENDANT_FIRST}": d_first,
                "{DEFENDANT_SECOND}": d_second,
                "{DEFENDANT_THIRD_FOURTH}": d_third_fourth,
                "{PLAINTIFF_FROM}": p_from,
                "{PLAINTIFF_RESIDENT}": p_res,
                "{DEFENDANT_FROM}": d_from,
                "{DEFENDANT_RESIDENT}": d_res,
                "{AMOUNT}": amount,
                "{HIJRI_DATE}": greg_to_hijri(date.today()),
                "{GREGORIAN_DATE}": date.today().strftime("%Y/%m/%d"),
                "{CLERK_NAME}": clerk_name, 
                "{JUDGE_NAME}": judge_name,
                "{VERDICT_TEXT}": verdict_body
            }

            from doc_helpers import safe_replace_in_doc
            safe_replace_in_doc(doc, placeholders)
            doc.save(final_path)

            # 4. Update Database: Case Status and Session Status
            db.cur.execute("""
                UPDATE cms.court_case 
                SET status = 'منتهية' 
                WHERE case_id = %s
            """, (case_id,))
            
            if self.current_verdict_session_id:
                db.cur.execute("""
                    UPDATE cms.session 
                    SET status = 'Finished' 
                    WHERE session_id = %s
                """, (self.current_verdict_session_id,))

            # 5. DB Save Document/Verdict
            db.cur.execute(
                "INSERT INTO cms.document (document_type, file_path, uploaded_by, case_id, client_id) VALUES (%s, %s, %s, %s, %s)",
                (f"حكم {case_type}", final_path, self.current_user_id, case_id, client_id)
            )
            db.cur.execute(
                "INSERT INTO cms.verdict (verdict_date, verdict_text, document_path, case_id, judge_id) VALUES (%s, %s, %s, %s, %s)",
                (date.today(), verdict_body, final_path, case_id, self.current_user_id)
            )
            db.conn.commit()
            db.close()

            QMessageBox.information(self, "نجاح", f"تم إصدار الحكم بنجاح.\n- تم إغلاق القضية.\n- تم تحديث الإحصائيات.\n- تم إنشاء الملف بنظام القوالب.")
            
            # فتح الملف تلقائياً بعد الحفظ
            try:
                os.startfile(final_path)
            except Exception as e:
                print(f"Could not open file: {e}")

            # Reset current selection and refresh UI
            self.current_verdict_case_id = None
            self.current_verdict_session_id = None
            self._load_all_session_dates()
            self._back_to_calendar()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {e}")

    def _back_to_calendar(self):
        """Go back to calendar view."""
        self.set_active_button(self.btn_calendar_side)
        self._show_calendar_page()


    def log_out(self):
        if self.main_shell:
            self.main_shell.switch_to_login()
        else:
            self.close()
