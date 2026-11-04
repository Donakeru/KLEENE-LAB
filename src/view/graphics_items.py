"""Elementos gráficos que representan estados y transiciones."""

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QPainterPath,
                         QPainterPathStroker, QPen, QPolygonF)
from PyQt6.QtWidgets import (QGraphicsDropShadowEffect, QGraphicsEllipseItem,
                             QGraphicsItem, QGraphicsPathItem,
                             QGraphicsPolygonItem, QGraphicsSimpleTextItem,
                             QStyle)

from .constants import (DARK, FINAL_FILL, FONT, INITIAL, PENDING, PENDING_FILL,
                        R, SELECTED, SELECTED_FILL, STATE_FILL)


class EdgeLabel(QGraphicsItem):
    """Etiqueta de transición dibujada sobre una pastilla redondeada."""

    PAD_X, PAD_Y = 6, 2

    def __init__(self, text, parent):
        super().__init__(parent)
        self.text = text
        self.font = QFont(FONT, 9, QFont.Weight.DemiBold)
        metrics = QFontMetricsF(self.font)
        width = metrics.horizontalAdvance(text) + 2 * self.PAD_X
        height = metrics.height() + 2 * self.PAD_Y
        self.rect = QRectF(-width / 2, -height / 2, width, height)
        self.color = DARK

    def setBrush(self, brush):
        self.color = brush.color()
        self.update()

    def boundingRect(self):
        return self.rect.adjusted(-1, -1, 1, 1)

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(QColor(self.color.red(), self.color.green(),
                                   self.color.blue(), 70), 1))
        painter.setBrush(QBrush(QColor("white")))
        radius = self.rect.height() / 2
        painter.drawRoundedRect(self.rect, radius, radius)
        painter.setFont(self.font)
        painter.setPen(self.color)
        painter.drawText(self.rect, Qt.AlignmentFlag.AlignCenter, self.text)


class StateItem(QGraphicsEllipseItem):
    """Estado editable dentro de la escena del autómata."""

    def __init__(self, sid, x, y):
        super().__init__(-R, -R, 2 * R, 2 * R)
        self.sid = sid
        self.edges = []
        self.highlight = False
        self.setPos(x, y)
        self.setZValue(2)
        self.final = False
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(43, 39, 34, 40))
        self.setGraphicsEffect(shadow)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        label = QGraphicsSimpleTextItem(sid, self)
        label.setFont(QFont(FONT, 10, QFont.Weight.DemiBold))
        label.setBrush(QBrush(DARK))
        br = label.boundingRect()
        label.setPos(-br.width() / 2, -br.height() / 2)
        label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.update_style()

    def decorate(self, inicial, final):
        self.final = final
        self.inner = None
        if final:
            r = R - 5
            self.inner = QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r, self)
            self.inner.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        if inicial:
            p = QPainterPath()
            p.moveTo(-R - 42, 0)
            p.lineTo(-R - 10, 0)
            pen = QPen(INITIAL, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            line = QGraphicsPathItem(p, self)
            line.setPen(pen)
            head = QGraphicsPolygonItem(QPolygonF([
                QPointF(-R - 1, 0), QPointF(-R - 13, -6.5), QPointF(-R - 13, 6.5)]), self)
            head.setPen(QPen(Qt.PenStyle.NoPen))
            head.setBrush(QBrush(INITIAL))
            for item in (line, head):
                item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.update_style()

    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)

    def update_style(self):
        if self.highlight:
            color, fill = PENDING, PENDING_FILL
        elif self.isSelected():
            color, fill = SELECTED, SELECTED_FILL
        else:
            color, fill = DARK, FINAL_FILL if self.final else STATE_FILL
        width = 2 if color is DARK else 2.75
        self.setPen(QPen(color, width))
        self.setBrush(QBrush(fill))
        if getattr(self, "inner", None) is not None:
            self.inner.setPen(QPen(color, 1.75))

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
        self.label = EdgeLabel(", ".join(symbols), self)
        for child in (self.arrow, self.label):
            child.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        src.edges.append(self)
        if dst is not src:
            dst.edges.append(self)
        self.set_color(DARK)
        self.update_path()

    def set_color(self, color):
        self.setPen(QPen(color, 2 if color is DARK else 2.75,
                         Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
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
            bend = 40 if self.curved else self._auto_bend(a, b, normal, distance)
            control = (a + b) / 2 + normal * bend

            def toward(point, target):
                vector = target - point
                length = math.hypot(vector.x(), vector.y()) or 1.0
                return point + vector * (R / length)

            start, end = toward(a, control), toward(b, control)
            path.moveTo(start)
            path.quadTo(control, end)
            tip, direction = end, end - control
            middle = a * 0.25 + control * 0.5 + b * 0.25
            label_center = middle + normal * (16 if self.curved else 0)
            self.auto_bend = bend
        self.setPath(path)
        length = math.hypot(direction.x(), direction.y()) or 1.0
        dx, dy = direction.x() / length, direction.y() / length
        back = tip - QPointF(dx, dy) * 13
        perpendicular = QPointF(-dy, dx) * 6
        self.arrow.setPolygon(QPolygonF([tip, back + perpendicular, back - perpendicular]))
        self.label.setPos(label_center)

    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)

    def _obstacles(self):
        scene = self.src.scene()
        states = getattr(scene, "state_items", {}) if scene is not None else {}
        return [item.pos() for item in states.values()
                if item is not self.src and item is not self.dst]

    def _auto_bend(self, a, b, normal, distance):
        """Curvatura para que la flecha no pase por encima de otros estados.

        Las aristas de retorno (hacia la izquierda, como los λ de vuelta de una
        clausura) siempre se curvan, por debajo si es posible, igual que se
        dibujan a mano. El resto queda recta salvo que atraviese un estado.
        """
        obstacles = self._obstacles()
        middle = (a + b) / 2
        clearance = (R + 8) ** 2

        def clear(bend):
            control = middle + normal * bend
            for step in range(1, 20):
                t = step / 20
                point = a * ((1 - t) ** 2) + control * (2 * (1 - t) * t) + b * (t * t)
                for obstacle in obstacles:
                    dx, dy = point.x() - obstacle.x(), point.y() - obstacle.y()
                    if dx * dx + dy * dy < clearance:
                        return False
            return True

        backwards = b.x() < a.x() - R
        if not backwards and clear(0):
            return 0
        # Lado preferido: abajo para los retornos, arriba para los saltos.
        # Si el retorno sale de una rama superior, se curva hacia arriba para
        # no cruzar las ramas de abajo (y viceversa).
        below = 1 if normal.y() > 0 else -1
        if backwards:
            prefer = -below if a.y() < b.y() - R else below
        else:
            prefer = -below
        for factor in (0.18, 0.3, 0.45, 0.6, 0.8):
            for side in (prefer, -prefer):
                bend = side * max(45, factor * distance)
                if clear(bend):
                    return bend
        return prefer * max(45, 0.3 * distance)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(self.path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.set_color(SELECTED if self.isSelected() else DARK)
        return super().itemChange(change, value)
