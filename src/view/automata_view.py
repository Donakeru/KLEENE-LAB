"""Vista Qt para navegar por la escena del autómata."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView

from .constants import Mode


class AutomataView(QGraphicsView):
    """Vista con panorámica, zoom y ajuste automático."""

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing
                            | QPainter.RenderHint.TextAntialiasing)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._pan_last = None
        self._pan_button = None

    def _starts_pan(self, event):
        button = event.button()
        return (button == Qt.MouseButton.MiddleButton
                or (button == Qt.MouseButton.LeftButton
                    and self.scene().mode == Mode.PAN))

    def update_cursor(self):
        if self._pan_last is not None:
            return
        cursor = (Qt.CursorShape.OpenHandCursor
                  if self.scene().mode == Mode.PAN
                  else Qt.CursorShape.ArrowCursor)
        self.viewport().setCursor(cursor)

    def mousePressEvent(self, event):
        if self._starts_pan(event):
            self._pan_last = event.position().toPoint()
            self._pan_button = event.button()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._starts_pan(event):
            self.mousePressEvent(event)
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_last is not None:
            position = event.position().toPoint()
            delta = position - self._pan_last
            self._pan_last = position
            horizontal, vertical = self.horizontalScrollBar(), self.verticalScrollBar()
            horizontal.setValue(horizontal.value() - delta.x())
            vertical.setValue(vertical.value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pan_last is not None and event.button() == self._pan_button:
            self._pan_last = self._pan_button = None
            self.update_cursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def fit(self):
        rect = self.scene().itemsBoundingRect()
        if rect.isNull():
            self.resetTransform()
            self.centerOn(150, 150)
            return
        self.fitInView(rect.adjusted(-70, -70, 70, 70),
                       Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 1.5:
            self.resetTransform()
            self.centerOn(rect.center())
