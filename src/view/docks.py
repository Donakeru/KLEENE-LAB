"""Docks reutilizables que componen los paneles de la ventana principal."""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (QAbstractItemView, QCheckBox, QDockWidget,
                             QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                             QLabel, QLineEdit, QPushButton, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
                             QMenu)

from src.model import LAMBDA

from .tooling import ToolButton


class EditDock(QDockWidget):
    """Panel lateral con el alfabeto y las herramientas de edición."""

    def __init__(self, parent, mode_actions, alphabet_callback):
        super().__init__("Edición", parent)
        self._alphabet_callback = alphabet_callback
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        alphabet_group = QGroupBox("Alfabeto")
        alphabet_layout = QVBoxLayout(alphabet_group)
        alphabet_layout.addWidget(QLabel("Símbolos separados por coma:"))
        self.alpha_edit = QLineEdit()
        self.alpha_edit.returnPressed.connect(self._apply_alphabet)
        alphabet_layout.addWidget(self.alpha_edit)
        apply_button = QPushButton("Aplicar")
        apply_button.setProperty("primary", True)
        apply_button.clicked.connect(self._apply_alphabet)
        alphabet_layout.addWidget(apply_button)
        layout.addWidget(alphabet_group)

        tools_group = QGroupBox("Herramientas")
        grid = QGridLayout(tools_group)
        for index, action in enumerate(mode_actions):
            grid.addWidget(self._tool_button(action), index // 3, index % 3)
        layout.addWidget(tools_group)
        layout.addStretch(1)

        self.setWidget(widget)
        self.setMinimumWidth(220)
        parent.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self)

    @staticmethod
    def _tool_button(action):
        key = action.shortcuts()[0].toString() if action.shortcuts() else ""
        button = ToolButton(key)
        button.setDefaultAction(action)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setIconSize(QSize(28, 28))
        button.setFixedSize(52, 44)
        keys = " / ".join(shortcut.toString() for shortcut in action.shortcuts())
        button.setToolTip(f"{action.text()}  ({keys})")
        return button

    def _apply_alphabet(self):
        self._alphabet_callback(self.alpha_edit.text())

    def set_alphabet(self, alphabet):
        self.alpha_edit.setText(", ".join(alphabet))


class PropertiesDock(QDockWidget):
    """Panel inferior para editar el estado o transición seleccionados."""

    def __init__(self, parent, scene, controller, status_callback):
        super().__init__("Características", parent)
        self.scene = scene
        self.controller = controller
        self._status_callback = status_callback
        self.prop_sid = None
        self.prop_edge = None
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        self.prop_name = QLineEdit()
        self.prop_name.editingFinished.connect(self.prop_renombrar)
        self.prop_ini = QCheckBox()
        self.prop_ini.setStyleSheet("margin-left: 6px;")
        self.prop_ini.clicked.connect(self.prop_cambiar_inicial)
        self.prop_fin = QCheckBox()
        self.prop_fin.setStyleSheet("margin-left: 6px;")
        self.prop_fin.clicked.connect(self.prop_cambiar_final)

        self.edge_origen = QLabel()
        self.edge_destino = QLabel()
        self.edge_valor = QPushButton()
        self.edge_valor.setStyleSheet("text-align: left; padding: 3px 8px;")
        self.edge_menu = QMenu(self.edge_valor)
        self.edge_menu.aboutToShow.connect(self.armar_menu_valor)
        self.edge_valor.setMenu(self.edge_menu)
        for label in (self.edge_origen, self.edge_destino):
            label.setContentsMargins(8, 0, 0, 0)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.prop_stack = QStackedWidget()
        self.prop_stack.addWidget(self._tabla_propiedades([
            ("Nombre", self.prop_name),
            ("Estado inicial", self.prop_ini),
            ("Estado final", self.prop_fin),
        ]))
        self.prop_stack.addWidget(self._tabla_propiedades([
            ("Origen", self.edge_origen),
            ("Destino", self.edge_destino),
            ("Valor (símbolos)", self.edge_valor),
        ]))
        layout.addWidget(self.prop_stack)

        self.prop_hint = QLabel()
        self.prop_hint.setWordWrap(True)
        self.prop_hint.setStyleSheet("color: #7a7166;")
        layout.addWidget(self.prop_hint)
        layout.addStretch(1)

        self.setWidget(widget)
        self.setMaximumHeight(190)
        parent.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self)
        parent.setCorner(Qt.Corner.BottomLeftCorner,
                         Qt.DockWidgetArea.LeftDockWidgetArea)
        parent.setCorner(Qt.Corner.BottomRightCorner,
                         Qt.DockWidgetArea.RightDockWidgetArea)
        scene.selectionChanged.connect(self.actualizar_caracteristicas)
        self.actualizar_caracteristicas()

    def _tabla_propiedades(self, rows):
        table = QTableWidget(len(rows), 2)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 130)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setFixedHeight(28 * len(rows) + 2)
        for index, (name, editor) in enumerate(rows):
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item.setBackground(self.palette().alternateBase())
            table.setItem(index, 0, item)
            table.setCellWidget(index, 1, editor)
            table.setRowHeight(index, 28)
        return table

    def _status(self, message):
        self._status_callback(message)

    def actualizar_caracteristicas(self):
        ids = self.scene.selected_state_ids()
        edges = self.scene.selected_edges()
        model = self.scene.model
        if len(edges) == 1 and not ids:
            edge = edges[0]
            self.prop_sid = None
            self.prop_edge = (edge.src.sid, edge.dst.sid)
            self.prop_stack.setCurrentIndex(1)
            self.edge_origen.setText(edge.src.sid)
            self.edge_destino.setText(edge.dst.sid)
            self.edge_valor.setText(", ".join(edge.symbols))
            self.prop_hint.setText(
                "Elige los símbolos de la transición entre los del alfabeto "
                "(puedes marcar varios).")
            return

        self.prop_edge = None
        self.prop_stack.setCurrentIndex(0)
        if len(ids) == 1:
            sid = ids[0]
            self.prop_sid = sid
            is_initial = model.estado_inicial == sid
            locked = model.estado_inicial is not None and not is_initial
            self.prop_name.setEnabled(True)
            self.prop_fin.setEnabled(True)
            self.prop_ini.setEnabled(not locked)
            self.prop_name.setText(sid)
            self.prop_ini.setChecked(is_initial)
            self.prop_fin.setChecked(sid in model.estados_finales)
            self.prop_hint.setText(
                f"Ya existe un estado inicial ({model.estado_inicial}); desmárcalo allí "
                "para elegir otro." if locked else "")
        else:
            self.prop_sid = None
            for widget in (self.prop_name, self.prop_ini, self.prop_fin):
                widget.setEnabled(False)
            self.prop_name.setText("")
            self.prop_ini.setChecked(False)
            self.prop_fin.setChecked(False)
            empty = not ids and not edges
            self.prop_hint.setText(
                "Selecciona un estado o una transición para ver sus características."
                if empty else "Selecciona un solo elemento.")

    def prop_renombrar(self):
        sid = self.prop_sid
        if sid is None:
            return
        new_name = self.prop_name.text().strip()
        if not new_name or new_name == sid:
            self.prop_name.setText(sid)
            return
        if not self.controller.rename_state(sid, new_name):
            self._status(f"Ya existe un estado llamado «{new_name}».")
            self.prop_name.setText(sid)
            return
        self.scene.refresh(select=[new_name])

    def prop_cambiar_inicial(self, checked):
        sid, model = self.prop_sid, self.scene.model
        if sid is None:
            return
        if checked and model.estado_inicial not in (None, sid):
            self.actualizar_caracteristicas()
            return
        self.controller.set_initial(sid, checked)
        self.scene.refresh(select=[sid])

    def prop_cambiar_final(self, checked):
        sid, model = self.prop_sid, self.scene.model
        if sid is None:
            return
        self.controller.set_final(sid, checked)
        self.scene.refresh(select=[sid])

    def _simbolos_arista(self, origin, destination):
        return [symbol for (current_origin, symbol), destinations
                in self.scene.model.trans.items()
                if current_origin == origin and destination in destinations]

    def armar_menu_valor(self):
        self.edge_menu.clear()
        if self.prop_edge is None:
            return
        origin, destination = self.prop_edge
        alphabet = list(self.scene.model.alfabeto)
        if LAMBDA not in alphabet:
            alphabet.append(LAMBDA)
        current = self._simbolos_arista(origin, destination)
        for symbol in alphabet:
            action = self.edge_menu.addAction(symbol)
            action.setCheckable(True)
            action.setChecked(symbol in current)
            action.triggered.connect(
                lambda checked, symbol=symbol:
                self.prop_alternar_simbolo(symbol, checked))

    def prop_alternar_simbolo(self, symbol, checked):
        if self.prop_edge is None:
            return
        origin, destination = self.prop_edge
        if checked:
            self.controller.add_transition(origin, symbol, destination)
        else:
            if len(self._simbolos_arista(origin, destination)) <= 1:
                self._status(
                    "La transición necesita al menos un símbolo "
                    "(para quitarla usa Eliminar).")
                return
            self.controller.remove_transition(origin, symbol, destination)
        self.scene.refresh(select=[], select_edges=[(origin, destination)])


class RegexDock(QDockWidget):
    """Panel de conversión entre expresiones regulares y autómatas."""

    def __init__(self, parent, generate_callback, get_regex_callback,
                 steps_callback=None):
        super().__init__("Expresiones regulares", parent)
        self._generate_callback = generate_callback
        self._get_regex_callback = get_regex_callback
        self._steps_callback = steps_callback
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<b>ER → autómata</b>"))
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        self.regex_in = QLineEdit()
        self.regex_in.setPlaceholderText("ej.: (a+b)*abb")
        self.regex_in.returnPressed.connect(self._generate)
        lambda_button = QPushButton("λ")
        lambda_button.setFixedWidth(32)
        lambda_button.setToolTip("Insertar λ (cadena vacía)")
        lambda_button.clicked.connect(self._insert_lambda)
        row_layout.addWidget(self.regex_in)
        row_layout.addWidget(lambda_button)
        layout.addWidget(row)

        generate_button = QPushButton("Generar autómata")
        generate_button.setProperty("primary", True)
        generate_button.clicked.connect(self._generate)
        layout.addWidget(generate_button)
        help_label = QLabel(
            "Unión: ∪, U, | o +    Concatenación: implícita\n"
            "Vacía: λ    Conjunto vacío: ∅\n"
            "Ejemplo: a*(ab|ba)*")
        help_label.setStyleSheet("color: #7a7166; font-size: 9pt;")
        layout.addWidget(help_label)

        layout.addSpacing(12)
        layout.addWidget(QLabel("<b>Autómata → ER</b>"))
        get_regex_button = QPushButton("Obtener ER (lema de Arden)")
        get_regex_button.setProperty("primary", True)
        get_regex_button.clicked.connect(self._get_regex_callback)
        layout.addWidget(get_regex_button)
        self.regex_out = QLineEdit()
        self.regex_out.setReadOnly(True)
        self.regex_out.setPlaceholderText("aquí aparecerá la ER")
        layout.addWidget(self.regex_out)
        if steps_callback is not None:
            steps_button = QPushButton("Ver paso a paso")
            steps_button.setToolTip(
                "Muestra el sistema de ecuaciones y cada sustitución "
                "hasta llegar a la ER")
            steps_button.clicked.connect(self._steps_callback)
            layout.addWidget(steps_button)
        layout.addStretch(1)

        self.setWidget(widget)
        parent.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self)

    def _insert_lambda(self):
        self.regex_in.insert(LAMBDA)
        self.regex_in.setFocus()

    def _generate(self):
        self._generate_callback(self.regex_in.text())

    def set_output(self, value):
        self.regex_out.setText(value)
        self.regex_out.setCursorPosition(0)
