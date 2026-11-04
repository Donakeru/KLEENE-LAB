"""Tema visual claro y coherente para toda la aplicación."""

import os
import tempfile

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPalette, QPen, QPixmap
from PyQt6.QtWidgets import QStyleFactory

from .constants import (ACCENT, ACCENT_HOVER, ACCENT_LINE, ACCENT_PRESSED,
                        ACCENT_SOFT, BORDER, FONT, PANEL, SCROLL, SCROLL_HOVER,
                        SURFACE, TEXT, TEXT_DISABLED, TEXT_MUTED)


STYLESHEET = f"""
QMainWindow, QWidget {{
    color: {TEXT};
}}
QMainWindow {{
    background: {SURFACE};
}}
QMainWindow::separator {{
    background: {SURFACE};
    width: 6px;
    height: 6px;
}}

/* --- barra de herramientas ------------------------------------------ */
QToolBar {{
    background: {PANEL};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 4px 8px;
    spacing: 2px;
}}
QToolBar QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
}}
QToolBar QToolButton:hover {{
    background: {ACCENT_SOFT};
    border-color: {ACCENT_LINE};
}}
QToolBar::separator {{
    background: {BORDER};
    width: 1px;
    margin: 4px 8px;
}}

/* --- paneles -------------------------------------------------------- */
QDockWidget {{
    font-weight: 600;
}}
QDockWidget::title {{
    background: {PANEL};
    border-bottom: 1px solid {BORDER};
    padding: 8px 10px;
    text-align: left;
}}
QDockWidget > QWidget {{
    background: {PANEL};
    font-weight: normal;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {TEXT_MUTED};
}}
QLabel {{
    background: transparent;
}}

/* --- controles ------------------------------------------------------ */
QLineEdit {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}
QLineEdit:read-only {{
    background: {SURFACE};
    font-family: Consolas, monospace;
}}
QLineEdit:disabled {{
    color: {TEXT_DISABLED};
    background: {SURFACE};
}}
QPushButton {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton:hover {{
    background: {ACCENT_SOFT};
    border-color: {ACCENT_LINE};
}}
QPushButton:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton[primary="true"] {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: white;
    font-weight: 600;
}}
QPushButton[primary="true"]:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton::menu-indicator {{
    subcontrol-position: right center;
    right: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {SCROLL_HOVER};
    border-radius: 4px;
    background: white;
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
    image: url(__CHECK__);
}}
QCheckBox::indicator:disabled {{
    background: {SURFACE};
    border-color: {BORDER};
}}

/* --- botones de herramientas del panel ----------------------------- */
QGroupBox QToolButton {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QGroupBox QToolButton:hover {{
    background: {ACCENT_SOFT};
    border-color: {ACCENT_LINE};
}}
QGroupBox QToolButton:checked {{
    background: {ACCENT_PRESSED};
    border: 2px solid {ACCENT};
}}

/* --- tabla de características -------------------------------------- */
QTableWidget {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
}}
QTableWidget QLineEdit {{
    border: none;
    border-radius: 0;
}}
QTableWidget QPushButton {{
    border: none;
    border-radius: 0;
}}

/* --- otros ---------------------------------------------------------- */
QStatusBar {{
    background: {PANEL};
    border-top: 1px solid {BORDER};
    color: {TEXT_MUTED};
}}
QMenu {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 5px 24px 5px 24px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {ACCENT_SOFT};
    color: {TEXT};
}}
QToolTip {{
    background: {TEXT};
    color: white;
    border: none;
    padding: 4px 8px;
}}
QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
    width: 10px;
    height: 10px;
}}
QScrollBar::handle {{
    background: {SCROLL};
    border-radius: 5px;
    min-height: 30px;
    min-width: 30px;
}}
QScrollBar::handle:hover {{
    background: {SCROLL_HOVER};
}}
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
    width: 0;
    height: 0;
}}
"""


def _check_icon():
    """Dibuja la marca de verificación de las casillas y devuelve su ruta."""
    path = os.path.join(tempfile.gettempdir(), "kleene_lab_check.png")
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("white"), 4, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPolyline([QPointF(8, 17), QPointF(13.5, 22.5), QPointF(24, 10)])
    painter.end()
    pixmap.save(path)
    return path.replace("\\", "/")


def apply_theme(app):
    """Aplica estilo Fusion, paleta clara y hoja de estilos a la aplicación."""
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setFont(QFont(FONT, 10))

    palette = QPalette()
    role = QPalette.ColorRole
    palette.setColor(role.Window, QColor(SURFACE))
    palette.setColor(role.WindowText, QColor(TEXT))
    palette.setColor(role.Base, QColor("white"))
    palette.setColor(role.AlternateBase, QColor(SURFACE))
    palette.setColor(role.Text, QColor(TEXT))
    palette.setColor(role.Button, QColor("white"))
    palette.setColor(role.ButtonText, QColor(TEXT))
    palette.setColor(role.Highlight, QColor(ACCENT))
    palette.setColor(role.HighlightedText, QColor("white"))
    palette.setColor(role.ToolTipBase, QColor(TEXT))
    palette.setColor(role.ToolTipText, QColor("white"))
    palette.setColor(role.PlaceholderText, QColor(TEXT_DISABLED))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET.replace("__CHECK__", _check_icon()))
