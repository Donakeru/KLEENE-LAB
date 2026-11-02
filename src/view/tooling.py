"""Herramientas visuales de la barra de edición."""

import math

from PyQt6.QtCore import QRect, QPointF, QSize, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QIcon, QPainter, QPen,
                         QPixmap, QPolygonF)
from PyQt6.QtWidgets import QToolButton

from .constants import DARK, Mode, SELECTED


def make_icon(kind):
    """Dibuja el icono de una herramienta en una imagen HiDPI."""
    pixmap = QPixmap(64, 64)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(DARK, 2, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

    def arrow(x0, y0, x1, y1, color=DARK):
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(QBrush(color))
        length = math.hypot(x1 - x0, y1 - y0) or 1.0
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        bx, by = x1 - ux * 6, y1 - uy * 6
        painter.drawLine(QPointF(x0, y0), QPointF(bx, by))
        painter.drawPolygon(QPolygonF([
            QPointF(x1, y1),
            QPointF(bx - uy * 4, by + ux * 4),
            QPointF(bx + uy * 4, by - ux * 4),
        ]))

    if kind == Mode.SELECT:
        painter.setBrush(QBrush(DARK))
        painter.drawPolygon(QPolygonF([
            QPointF(9, 5), QPointF(9, 25), QPointF(14, 20),
            QPointF(18, 28), QPointF(21, 26.5), QPointF(17, 19),
            QPointF(24, 19),
        ]))
    elif kind == Mode.PAN:
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            arrow(16 + dx * 2, 16 + dy * 2,
                  16 + dx * 12, 16 + dy * 12)
    elif kind == Mode.STATE:
        painter.drawEllipse(QPointF(16, 16), 11, 11)
        painter.setPen(QPen(SELECTED, 2.5, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(16, 10), QPointF(16, 22))
        painter.drawLine(QPointF(10, 16), QPointF(22, 16))
    elif kind == Mode.TRANS:
        painter.drawEllipse(QPointF(7, 24), 5, 5)
        painter.drawEllipse(QPointF(25, 8), 5, 5)
        arrow(11, 20, 21, 12)
    elif kind == Mode.DELETE:
        red = QColor("#c62828")
        painter.setPen(QPen(red, 2, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(QPointF(7, 9), QPointF(25, 9))
        painter.drawPolyline(QPolygonF([
            QPointF(13, 9), QPointF(13, 5.5), QPointF(19, 5.5), QPointF(19, 9),
        ]))
        painter.drawPolyline(QPolygonF([
            QPointF(9.5, 9), QPointF(11, 26.5), QPointF(21, 26.5), QPointF(22.5, 9),
        ]))
        painter.drawLine(QPointF(14, 13), QPointF(14, 22))
        painter.drawLine(QPointF(18, 13), QPointF(18, 22))
    painter.end()
    return QIcon(pixmap)


class ToolButton(QToolButton):
    """Botón de herramienta que muestra su tecla en la esquina superior."""

    def __init__(self, tecla=""):
        super().__init__()
        self.tecla = tecla

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.tecla:
            return
        painter = QPainter(self)
        painter.setFont(QFont("Sans", 8, QFont.Weight.Bold))
        painter.setPen(QColor("#666666"))
        painter.drawText(QRect(5, 2, 16, 14),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         self.tecla)
        painter.end()
