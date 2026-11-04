"""Escena interactiva para editar autómatas."""

import math
from collections import defaultdict

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsLineItem, QGraphicsScene,
                             QInputDialog, QMenu, QMessageBox)

from src.model import LAMBDA

from .constants import CANVAS_BG, CANVAS_DOT, DARK, HINTS, PENDING, Mode
from .graphics_items import EdgeItem, StateItem


class AutomataScene(QGraphicsScene):
    """Coordina la interacción gráfica y las mutaciones del modelo."""

    modified = pyqtSignal()
    status = pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.model = controller.model
        self.mode = Mode.SELECT
        self.pending = None
        self.temp_line = None
        self.state_items = {}
        self.setSceneRect(-2000, -2000, 5000, 4000)
        self.refresh()

    def grow_scene_rect(self):
        """Amplía el área desplazable para que contenga todos los estados
        (los autómatas generados pueden ser muy anchos)."""
        bounds = self.itemsBoundingRect().adjusted(-1500, -1500, 1500, 1500)
        if not self.sceneRect().contains(bounds):
            self.setSceneRect(self.sceneRect().united(bounds))

    def dialog_parent(self):
        views = self.views()
        return views[0] if views else None

    def set_model(self, model):
        self.model = model
        self.refresh(select=[])

    def set_mode(self, mode):
        self.mode = mode
        self.cancel_pending()
        for item in self.state_items.values():
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
                         mode == Mode.SELECT)
        for view in self.views():
            view.update_cursor()
        self.status.emit(HINTS[mode])

    def changed(self, select=None, select_edges=None):
        """Reconstruye la vista y conserva la selección indicada."""
        self.refresh(select, select_edges)
        self.modified.emit()

    def on_state_moved(self, sid, x, y):
        self.controller.move_state(sid, x, y)

    def find_item(self, pos):
        for item in self.items(pos):
            while item is not None and not isinstance(item, (StateItem, EdgeItem)):
                item = item.parentItem()
            if item is not None:
                return item
        return None

    def refresh(self, select=None, select_edges=None):
        ids = set(select) if select is not None else set(self.selected_state_ids())
        if select_edges is not None:
            keys = set(select_edges)
        elif select is None:
            keys = {(edge.src.sid, edge.dst.sid)
                    for edge in self.selected_edges()}
        else:
            keys = set()

        self.blockSignals(True)
        self.pending = None
        self.temp_line = None
        self.clear()
        self.state_items = {}
        model = self.model
        for sid, (x, y) in model.estados.items():
            item = StateItem(sid, x, y)
            item.decorate(sid == model.estado_inicial,
                          sid in model.estados_finales)
            self.addItem(item)
            self.state_items[sid] = item

        groups = defaultdict(list)
        for (origin, symbol), destinations in model.trans.items():
            for destination in destinations:
                groups[(origin, destination)].append(symbol)
        order = {symbol: index for index, symbol in enumerate(model.alfabeto)}
        edge_items = {}
        for (origin, destination), symbols in groups.items():
            symbols.sort(key=lambda symbol: order.get(symbol, 1e9))
            curved = (origin != destination
                      and (destination, origin) in groups)
            edge = EdgeItem(self.state_items[origin], self.state_items[destination],
                            symbols, curved)
            self.addItem(edge)
            edge_items[(origin, destination)] = edge

        for item in self.state_items.values():
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
                         self.mode == Mode.SELECT)
        self.grow_scene_rect()
        for sid in ids:
            if sid in self.state_items:
                self.state_items[sid].setSelected(True)
        for key in keys:
            if key in edge_items:
                edge_items[key].setSelected(True)
        self.blockSignals(False)
        self.selectionChanged.emit()

    def add_state_at(self, pos):
        self.controller.add_state(
            self.controller.next_state_id(), pos.x(), pos.y())

    def ask_transition(self, origin, destination):
        model = self.model
        if not model.alfabeto:
            QMessageBox.warning(
                self.dialog_parent(), "Sin alfabeto",
                "Define primero el alfabeto en el panel lateral.")
            return
        symbol, accepted = QInputDialog.getItem(
            self.dialog_parent(), "Nueva transición",
            f"Símbolo para {origin} → {destination} (λ = transición vacía):",
            model.alfabeto + [LAMBDA], 0, False)
        if not accepted:
            return
        if self.controller.add_transition(origin, symbol, destination):
            return
        self.status.emit(
            f"Ya existe la transición {origin} --{symbol}--> {destination}.")

    def delete_edge(self, edge, ask=True):
        symbols = list(edge.symbols)
        if ask and len(symbols) > 1:
            all_symbols = "(todos)"
            selected, accepted = QInputDialog.getItem(
                self.dialog_parent(), "Eliminar transición",
                "¿Qué símbolo eliminar?", [all_symbols] + symbols, 0, False)
            if not accepted:
                return
            if selected != all_symbols:
                symbols = [selected]
        self.controller.remove_transitions([
            (edge.src.sid, symbol, edge.dst.sid) for symbol in symbols])

    def delete_item(self, item):
        if isinstance(item, StateItem):
            self.controller.remove_state(item.sid)
        elif isinstance(item, EdgeItem):
            self.delete_edge(item)

    def delete_selected(self):
        selected = self.selectedItems()
        states = [item.sid for item in selected if isinstance(item, StateItem)]
        edges = [(item.src.sid, item.dst.sid, list(item.symbols))
                 for item in selected if isinstance(item, EdgeItem)]
        if not states and not edges:
            return
        transitions = [
            (origin, symbol, destination)
            for origin, destination, symbols in edges
            for symbol in symbols
        ]
        if transitions:
            self.controller.remove_transitions(transitions)
        if states:
            self.controller.remove_states(states)

    def rename_state(self, sid):
        new_name, accepted = QInputDialog.getText(
            self.dialog_parent(), "Renombrar estado", "Nuevo nombre:", text=sid)
        new_name = new_name.strip()
        if not accepted or not new_name or new_name == sid:
            return
        if not self.controller.rename_state(sid, new_name):
            QMessageBox.warning(
                self.dialog_parent(), "Nombre repetido",
                f"Ya existe un estado llamado «{new_name}».")
            return
        self.refresh(select=[new_name])

    def cancel_pending(self):
        if self.pending is not None:
            self.pending.highlight = False
            self.pending.update_style()
        if self.temp_line is not None:
            self.removeItem(self.temp_line)
        self.pending = None
        self.temp_line = None

    def selected_state_ids(self):
        return [item.sid for item in self.selectedItems()
                if isinstance(item, StateItem)]

    def selected_edges(self):
        return [item for item in self.selectedItems()
                if isinstance(item, EdgeItem)]

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and self.mode != Mode.SELECT):
            pos = event.scenePos()
            item = self.find_item(pos)
            if self.mode == Mode.STATE:
                if item is None:
                    self.add_state_at(pos)
            elif self.mode == Mode.TRANS:
                self.handle_trans_click(item, pos)
            elif self.mode == Mode.DELETE and item is not None:
                self.delete_item(item)
            event.accept()
            return
        super().mousePressEvent(event)

    def handle_trans_click(self, item, pos):
        if not isinstance(item, StateItem):
            self.cancel_pending()
            return
        if self.pending is None:
            self.pending = item
            item.highlight = True
            item.update_style()
            self.temp_line = QGraphicsLineItem(
                item.pos().x(), item.pos().y(), pos.x(), pos.y())
            self.temp_line.setPen(QPen(PENDING, 2, Qt.PenStyle.DashLine,
                                       Qt.PenCapStyle.RoundCap))
            self.addItem(self.temp_line)
            self.status.emit("Ahora haz clic en el estado destino.")
        else:
            source = self.pending
            self.cancel_pending()
            self.ask_transition(source.sid, item.sid)

    def mouseMoveEvent(self, event):
        if self.temp_line is not None and self.pending is not None:
            anchor, position = self.pending.pos(), event.scenePos()
            self.temp_line.setLine(anchor.x(), anchor.y(),
                                   position.x(), position.y())
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and self.mode == Mode.SELECT):
            item = self.find_item(event.scenePos())
            if item is None:
                self.add_state_at(event.scenePos())
                event.accept()
                return
            if isinstance(item, StateItem):
                self.rename_state(item.sid)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
        elif event.key() == Qt.Key.Key_Escape:
            self.cancel_pending()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        item = self.find_item(event.scenePos())
        menu = QMenu()
        model = self.model
        if isinstance(item, StateItem):
            sid = item.sid
            initial_action = menu.addAction(
                "Quitar estado inicial" if model.estado_inicial == sid
                else "Marcar como estado inicial")
            if model.estado_inicial not in (None, sid):
                initial_action.setEnabled(False)
                initial_action.setText(
                    f"Marcar como estado inicial (ya existe: {model.estado_inicial})")
            final_action = menu.addAction(
                "Quitar de estados finales" if sid in model.estados_finales
                else "Marcar como estado final")
            menu.addSeparator()
            rename_action = menu.addAction("Renombrar…")
            delete_action = menu.addAction("Eliminar estado")
            selected = menu.exec(event.screenPos())
            if selected is initial_action:
                self.controller.toggle_initial(sid)
            elif selected is final_action:
                self.controller.toggle_final(sid)
            elif selected is rename_action:
                self.rename_state(sid)
            elif selected is delete_action:
                self.delete_item(item)
        elif isinstance(item, EdgeItem):
            one_action = (menu.addAction("Eliminar un símbolo…")
                          if len(item.symbols) > 1 else None)
            all_action = menu.addAction("Eliminar transición")
            selected = menu.exec(event.screenPos())
            if selected is not None and selected is one_action:
                self.delete_edge(item, ask=True)
            elif selected is all_action:
                self.delete_edge(item, ask=False)
        else:
            new_action = menu.addAction("Agregar estado aquí")
            if menu.exec(event.screenPos()) is new_action:
                self.add_state_at(event.scenePos())
        event.accept()

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, CANVAS_BG)
        step = 25
        scale = painter.worldTransform().m11() or 1.0
        while step * scale < 16:
            step *= 2
        painter.setPen(QPen(CANVAS_DOT, 2, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        left = int(math.floor(rect.left() / step)) * step
        top = int(math.floor(rect.top() / step)) * step
        points = []
        y = top
        while y < rect.bottom():
            x = left
            while x < rect.right():
                points.append(QPointF(x, y))
                x += step
            y += step
        if len(points) < 40000:
            painter.drawPoints(points)
