from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                              QLabel, QLineEdit, QPushButton,
                              QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
                              QGraphicsBlurEffect)
from PyQt5.QtGui import QPixmap, QCursor, QPainter, QImage, QColor, QPainterPath, QIcon
from PyQt5.QtCore import Qt, QRect, QSize


# ── أيقونات SVG مدمجة ───────────────────────────────────────────────
USER_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
  stroke="white" stroke-opacity="0.75" stroke-width="1.8"
  stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="8" r="4"/>
  <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
</svg>"""

KEY_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
  stroke="white" stroke-opacity="0.75" stroke-width="1.8"
  stroke-linecap="round" stroke-linejoin="round">
  <circle cx="8" cy="12" r="4"/>
  <path d="M12 12h8M18 10v4M16 10v4"/>
</svg>"""


def _svg_to_pixmap(svg_bytes: bytes, size: int = 22) -> QPixmap:
    try:
        from PyQt5 import QtSvg
        renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg_bytes))
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        renderer.render(p)
        p.end()
        return pix
    except Exception:
        return QPixmap()


class IconLineEdit(QLineEdit):
    """QLineEdit يرسم أيقونة SVG بيده على يمين الحقل"""

    ICON_SIZE   = 22
    ICON_MARGIN = 14   # مسافة الأيقونة من الحافة اليمنى

    def __init__(self, placeholder: str, svg_bytes: bytes,
                 password: bool = False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFixedHeight(54)
        if password:
            self.setEchoMode(QLineEdit.Password)

        self._icon_pix = _svg_to_pixmap(svg_bytes, self.ICON_SIZE)

        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.18);
                border: 1.5px solid rgba(255,255,255,0.45);
                border-radius: 13px;
                padding: 14px 18px;
                font-size: 17px;
                font-family: 'Alyamama', 'Cairo', Arial;
                color: #ffffff;
            }
            QLineEdit:focus {
                background-color: rgba(255,255,255,0.28);
                border: 2px solid rgba(255,255,255,0.80);
            }
        """)

        # setTextMargins بيحجز مساحة يمين للأيقونة وبيؤثر على النص والـ placeholder معاً
        right_margin = self.ICON_SIZE + self.ICON_MARGIN - 4
        self.setTextMargins(0, 0, right_margin, 0)

    def paintEvent(self, event):
        super().paintEvent(event)   # ارسم الحقل أولاً
        if self._icon_pix.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # موقع الأيقونة: يمين الحقل، مركزها عمودياً
        x = self.width() - self.ICON_SIZE - self.ICON_MARGIN
        y = (self.height() - self.ICON_SIZE) // 2
        painter.drawPixmap(x, y, self._icon_pix)
        painter.end()


class ModernLoginWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_image = QImage("icons/background.jpeg")
        self.init_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.bg_image.isNull():
            painter.drawImage(self.rect(), self.bg_image)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))
        super().paintEvent(event)

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        h_center = QHBoxLayout()
        h_center.addStretch(1)

        self.anim_container = QWidget()
        self.anim_container.setFixedSize(640, 680)
        anim_layout = QVBoxLayout(self.anim_container)
        anim_layout.setContentsMargins(0, 0, 0, 0)
        anim_layout.setAlignment(Qt.AlignCenter)

        self.card = FrostedCard(self)
        self.card.setFixedSize(560, 610)

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(55)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 14)
        self.card.setGraphicsEffect(shadow)

        anim_layout.addWidget(self.card)
        h_center.addWidget(self.anim_container)
        h_center.addStretch(1)
        outer.addLayout(h_center)
        outer.addStretch(1)

        # ── محتوى الكارد ───────────────────────────────────────────────
        self.cardLayout = QVBoxLayout(self.card)
        self.cardLayout.setContentsMargins(55, 45, 55, 45)
        self.cardLayout.setSpacing(0)

        # شعار
        self.cardIcon = QLabel()
        logo_pix = QPixmap("icons/scales.png")
        if not logo_pix.isNull():
            self.cardIcon.setPixmap(
                logo_pix.scaled(110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.cardIcon.setAlignment(Qt.AlignCenter)
        self.cardLayout.addWidget(self.cardIcon)
        self.cardLayout.addSpacing(14)

        self.loginLabel = QLabel(" تسـجـيـل الـدخـول")
        self.loginLabel.setLayoutDirection(Qt.RightToLeft)
        self.loginLabel.setStyleSheet("""
            font-size: 34px; font-weight: bold;
            color: #ffffff;
            font-family: 'Alyamama', 'Cairo', Arial;
        """)
        self.loginLabel.setAlignment(Qt.AlignCenter)
        self.cardLayout.addWidget(self.loginLabel)
        self.cardLayout.addSpacing(5)

        self.courtTitle = QLabel("المحكمة الشرعية")
        self.courtTitle.setLayoutDirection(Qt.RightToLeft)
        self.courtTitle.setStyleSheet("""
            font-size: 16px; color: rgba(255,255,255,0.80);
            font-family: 'Alyamama', 'Cairo', Arial;
        """)
        self.courtTitle.setAlignment(Qt.AlignCenter)
        self.cardLayout.addWidget(self.courtTitle)

        self.cardLayout.addStretch(1)

        # ── حقول الإدخال مع الأيقونات ──────────────────────────────────
        self.username = IconLineEdit("اسم المستخدم", USER_SVG, password=False)
        self.cardLayout.addWidget(self.username)
        self.cardLayout.addSpacing(16)

        self.password = IconLineEdit("كلمة المرور", KEY_SVG, password=True)
        self.cardLayout.addWidget(self.password)
        self.cardLayout.addSpacing(28)

        # ── زر تسجيل الدخول ────────────────────────────────────────────
        self.loginButton = QPushButton("تسجيل الدخول")
        self.loginButton.setFixedHeight(56)
        self.loginButton.setCursor(QCursor(Qt.PointingHandCursor))
        self.loginButton.setStyleSheet("""
            QPushButton {
                background-color: #c8b89a;
                color: #2c1f1a;
                border-radius: 13px;
                font-size: 20px;
                font-family: 'Alyamama', 'Cairo', Arial;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover   { background-color: #d9cbb0; }
            QPushButton:pressed { background-color: #b0a082; }
        """)
        self.cardLayout.addWidget(self.loginButton)
        self.cardLayout.addStretch(1)

        # ── Fade-in ────────────────────────────────────────────────────
        self.fade_effect = QGraphicsOpacityEffect(self.anim_container)
        self.anim_container.setGraphicsEffect(self.fade_effect)
        self.fade_effect.setOpacity(0)

        self.anim = QtCore.QPropertyAnimation(self.fade_effect, b"opacity")
        self.anim.setDuration(1200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.anim.finished.connect(self._cleanup_anim)
        QtCore.QTimer.singleShot(150, self.anim.start)

    def _cleanup_anim(self):
        self.anim_container.setGraphicsEffect(None)


class FrostedCard(QWidget):
    RADIUS = 26.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), self.RADIUS, self.RADIUS)
        painter.setClipPath(path)

        parent = self.parent()
        if parent and hasattr(parent, 'bg_image') and not parent.bg_image.isNull():
            bg = parent.bg_image
            pw, ph = parent.width(), parent.height()
            iw, ih = bg.width(), bg.height()
            if pw > 0 and ph > 0:
                pos = self.mapTo(parent, QtCore.QPoint(0, 0))
                sx, sy = iw / pw, ih / ph
                src_rect = QtCore.QRectF(
                    pos.x() * sx, pos.y() * sy,
                    self.width() * sx, self.height() * sy)
                cropped = bg.copy(src_rect.toRect())
                blurred = self._blur_image(cropped, 18)
                painter.drawImage(self.rect(), blurred)

        painter.fillRect(self.rect(), QColor(20, 10, 10, 120))

        painter.setClipping(False)
        painter.setPen(QtGui.QPen(QColor(255, 255, 255, 70), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        super().paintEvent(event)

    @staticmethod
    def _blur_image(img: QImage, radius: int) -> QImage:
        pix = QPixmap.fromImage(img)
        scene = QtWidgets.QGraphicsScene()
        item  = QtWidgets.QGraphicsPixmapItem(pix)
        blur  = QGraphicsBlurEffect()
        blur.setBlurRadius(radius)
        blur.setBlurHints(QGraphicsBlurEffect.QualityHint)
        item.setGraphicsEffect(blur)
        scene.addItem(item)
        result = QImage(img.size(), QImage.Format_ARGB32)
        result.fill(Qt.transparent)
        p = QPainter(result)
        scene.render(p, QtCore.QRectF(result.rect()),
                     QtCore.QRectF(0, 0, pix.width(), pix.height()))
        p.end()
        return result