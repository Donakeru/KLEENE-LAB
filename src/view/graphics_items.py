"""Elementos gráficos que representan estados y transiciones."""

import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QPainterPath, QPainterPathStroker,
                         QPen, QPolygonF)
from PyQt6.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem,
                             QGraphicsPathItem, QGraphicsPolygonItem,
                             QGraphicsSimpleTextItem)

from .constants import DARK, PENDING, R, SELECTED


class StateItem(QGraphicsEllipseItem):
    """Estado editable dentro de la escena del autómata."""

    def __init__(self, sid, x, y):
        super().__init__(-R, -R, 2 * R, 2 * R)
        self.sid = sid
        self.edges = []
        self.highlight = False
        self.setPos(x, y)
        self.setZValue(2)
        self.setBrush(QBrush(QColor("white")))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        label = QGraphicsSimpleTextItem(sid, self)
        label.setFont(QFont("Sans", 10, QFont.Weight.Bold))
        br = label.boundingRect()
        label.setPos(-br.width() / 2, -br.height() / 2)
        label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.update_style()

    def decorate(self, inicial, final):
        if final:
            r = R - 6
            inner = QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r, self)
            inner.setPen(QPen(DARK, 2))
            inner.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        if inicial:
            p = QPainterPath()
            p.moveTo(-R - 40, 0)
            p.lineTo(-R, 0)
            p.moveTo(-R, 0)
            p.lineTo(-R - 11, -6)
            p.lineTo(-R - 11, 6)
            p.closeSubpath()
            arrow = QGraphicsPathItem(p, self)
            arrow.setPen(QPen(DARK, 2))
            arrow.setBrush(QBrush(DARK))
            arrow.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def update_style(self):
        color = PENDING if self.highlight else (SELECTED if self.isSelected() else DARK)
        self.setPen(QPen(color, 2.5 if color is not DARK else 2))

    def itemChange(self, change, value):
        graphics_change = QGraphicsItem.GraphicsItemChange
        if change == graphics_change.ItemPositionHasChanged and self.scene() is not None:
            p = self.pos()
            self.scene().on_state_moved(self.sid, p.x(), p.y())
            for edge in self.edges:
                edge.update_path()
        elif change == graphics_change.ItemSelectedHasChanged:
            self.update_style()
        return super().itemChange(change, value)


class EdgeItem(QGraphicsPathItem):
    """Flecha entre dos estados que agrupa sus símbolos."""

    def __init__(self, src, dst, symbols, curved):
        super().__init__()
        self.src, self.dst, self.symbols, self.curved = src, dst, symbols, curved
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.arrow = QGraphicsPolygonItem(self)
        self.arrow.setPen(QPen(Qt.PenStyle.NoPen))
        self.label = QGraphicsSimpleTextItem(", ".join(symbols), self)
        self.label.setFont(QFont("Sans", 10, QFont.Weight.Bold))
        for child in (self.arrow, self.label):
            child.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        src.edges.append(self)
        if dst is not src:
            dst.edges.append(self)
        self.set_color(DARK)
        self.update_path()

    def set_color(self, color):
        self.setPen(QPen(color, 2))
        self.arrow.setBrush(QBrush(color))
        self.label.setBrush(QBrush(color))

    def update_path(self):
        a, b = self.src.pos(), self.dst.pos()
        path = QPainterPath()
        if self.src is self.dst:
            angle_point = lambda degrees: QPointF(
                R * math.cos(math.radians(degrees)),
                R * math.sin(math.radians(degrees)))
            start, end = a + angle_point(-125), a + angle_point(-55)
            control1 = a + QPointF(-45, -R - 55)
            control2 = a + QPointF(45, -R - 55)
            path.moveTo(start)
            path.cubicTo(control1, control2, end)
            tip, direction = end, end - control2
            label_center = a + QPointF(0, -R - 47)
        else:
            delta = b - a
            distance = math.hypot(delta.x(), delta.y()) or 1.0
            ux, uy = delta.x() / distance, delta.y() / distance
            normal = QPointF(-uy, ux)
            control = (a + b) / 2 + normal * (40 if self.curved else 0)

            def toward(point, target):
                vector = target - point
                length = math.hypot(vector.x(), vector.y()) or 1.0
                return point + vector * (R / length)

            start, end = toward(a, control), toward(b, control)
            path.moveTo(start)
            path.quadTo(control, end)
            tip, direction = end, end - control
            middle = a * 0.25 + control * 0.5 + b * 0.25
            label_center = middle + normal * 14
        self.setPath(path)
        length = math.hypot(direction.x(), direction.y()) or 1.0
        dx, dy = direction.x() / length, direction.y() / length
        back = tip - QPointF(dx, dy) * 12
        perpendicular = QPointF(-dy, dx) * 5.5
        self.arrow.setPolygon(QPolygonF([tip, back + perpendicular, back - perpendicular]))
        bounds = self.label.boundingRect()
        self.label.setPos(label_center.x() - bounds.width() / 2,
                          label_center.y() - bounds.height() / 2)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(self.path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.set_color(SELECTED if self.isSelected() else DARK)
        return super().itemChange(change, value)
