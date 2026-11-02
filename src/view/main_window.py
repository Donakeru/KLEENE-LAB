"""Ventana principal: compone la vista y se comunica con el controlador."""

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QToolBar

from src.algorithms.regex_tools import ErrorSintaxis
from src.controller.automata_controller import AutomataController
from src.model import Automata

from .automata_view import AutomataView
from .constants import EJEMPLO, Mode
from .docks import EditDock, PropertiesDock, RegexDock
from .scene import AutomataScene
from .tooling import make_icon


class MainWindow(QMainWindow):
    """Compositor de la interfaz y coordinador de interacción Qt."""

    def __init__(self, model=None):
        super().__init__()
        self.path = None
        self.dirty = False
        initial_model = model or Automata.from_dict(EJEMPLO)
        self.controller = AutomataController(initial_model)
        self.scene = AutomataScene(self.controller)
        self.view = AutomataView(self.scene)
        self.setCentralWidget(self.view)
        self.resize(1100, 700)

        self.controller.model_changed.connect(self._on_model_changed)
        self.controller.modified.connect(self.on_modified)
        self.controller.status.connect(self.statusBar().showMessage)
        self.scene.status.connect(self.statusBar().showMessage)

        self.build_actions()
        self.edit_dock = EditDock(self, self.mode_actions, self.apply_alphabet)
        self.regex_dock = RegexDock(self, self.generar_desde_er, self.obtener_er)
        self.properties_dock = PropertiesDock(
            self, self.scene, self.controller, self.statusBar().showMessage)
        self.scene.set_mode(Mode.SELECT)
        self.sync_alphabet()
        self.update_title()
        QTimer.singleShot(0, self.view.fit)

    def _on_model_changed(self, model):
        """Actualiza las vistas cuando el controlador reemplaza el modelo."""
        self.scene.set_model(model)
        if hasattr(self, "edit_dock"):
            self.sync_alphabet()

    def build_actions(self):
        """Construye la barra principal y las acciones de edición."""
        toolbar = QToolBar("Herramientas")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        def action(text, slot, shortcut=None, checkable=False):
            item = QAction(text, self)
            item.setCheckable(checkable)
            if shortcut:
                keys = [shortcut] if isinstance(shortcut, str) else shortcut
                item.setShortcuts([QKeySequence(key) for key in keys])
            item.triggered.connect(lambda _checked=False: slot())
            return item

        for text, slot, shortcut in [
            ("Nuevo", self.new_file, "Ctrl+N"),
            ("Abrir…", self.open_file, "Ctrl+O"),
            ("Guardar", self.save_file, "Ctrl+S"),
            ("Guardar como…", self.save_file_as, "Ctrl+Shift+S"),
        ]:
            toolbar.addAction(action(text, slot, shortcut))
        toolbar.addSeparator()
        toolbar.addAction(action("Ajustar vista", self.view.fit, "Ctrl+0"))

        group = QActionGroup(self)
        group.setExclusive(True)
        self.mode_actions = []
        for text, mode, shortcut in [
            ("Mover vista (arrastrar)", Mode.PAN, ("1", "H")),
            ("Seleccionar / mover", Mode.SELECT, ("2", "V")),
            ("Agregar estado", Mode.STATE, ("3", "S")),
            ("Agregar transición", Mode.TRANS, ("4", "T")),
            ("Eliminar", Mode.DELETE, ("5", "D")),
        ]:
            item = action(
                text,
                lambda mode=mode: self.scene.set_mode(mode),
                shortcut,
                checkable=True)
            item.setIcon(make_icon(mode))
            group.addAction(item)
            self.mode_actions.append(item)
            if mode == Mode.SELECT:
                item.setChecked(True)

    # --- conversiones -----------------------------------------------------
    def generar_desde_er(self, expression):
        try:
            model = self.controller.regex_to_automaton(expression)
        except ErrorSintaxis as error:
            QMessageBox.warning(self, "Expresión inválida", str(error))
            return
        except NotImplementedError as error:
            QMessageBox.information(self, "Algoritmo pendiente", str(error))
            return

        if self.scene.model.estados:
            result = QMessageBox.question(
                self,
                "Reemplazar autómata",
                "Se reemplazará el autómata actual por el generado. ¿Continuar?")
            if result != QMessageBox.StandardButton.Yes:
                return
        self.load_model(model, dirty=True)
        self.statusBar().showMessage(
            f"Autómata generado: {len(model.estados)} estados.")

    def obtener_er(self):
        if self.scene.model.estado_inicial is None:
            QMessageBox.warning(
                self,
                "Sin estado inicial",
                "Marca un estado inicial antes de obtener la ER.")
            return
        try:
            expression = self.controller.automaton_to_regex()
        except NotImplementedError as error:
            QMessageBox.information(self, "Algoritmo pendiente", str(error))
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error en automaton_to_regex",
                f"{type(error).__name__}: {error}")
            return
        self.regex_dock.set_output(expression)
        self.statusBar().showMessage("ER obtenida del autómata.")

    # --- alfabeto ---------------------------------------------------------
    def sync_alphabet(self):
        self.edit_dock.set_alphabet(self.controller.model.alfabeto)

    def apply_alphabet(self, text):
        alphabet = list(dict.fromkeys(
            symbol.strip() for symbol in text.split(",") if symbol.strip()))
        affected = self.controller.transitions_using_outside(alphabet)
        if affected:
            result = QMessageBox.question(
                self,
                "Cambiar alfabeto",
                f"Se eliminarán {affected} transición(es) que usan símbolos que ya no "
                "están en el alfabeto. ¿Continuar?")
            if result != QMessageBox.StandardButton.Yes:
                self.sync_alphabet()
                return
        self.controller.set_alphabet(alphabet)

    # --- archivos ---------------------------------------------------------
    def update_title(self):
        name = self.path or "sin título"
        self.setWindowTitle(f"Editor de autómatas — {name}{' *' if self.dirty else ''}")

    def on_modified(self):
        if not self.dirty:
            self.dirty = True
            self.update_title()

    def confirm_discard(self):
        if not self.dirty:
            return True
        result = QMessageBox.question(
            self,
            "Cambios sin guardar",
            "¿Guardar los cambios antes de continuar?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel)
        if result == QMessageBox.StandardButton.Save:
            return self.save_file()
        return result == QMessageBox.StandardButton.Discard

    def load_model(self, model, path=None, dirty=False):
        self.controller.replace_model(model, modified=False)
        self.path, self.dirty = path, dirty
        self.sync_alphabet()
        self.update_title()
        QTimer.singleShot(0, self.view.fit)

    def new_file(self):
        if self.confirm_discard():
            self.controller.new_model()
            self.path, self.dirty = None, False
            self.update_title()
            QTimer.singleShot(0, self.view.fit)

    def open_file(self):
        if not self.confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir autómata", "", "JSON (*.json);;Todos (*)")
        if path:
            self.open_path(path)

    def open_path(self, path):
        try:
            self.controller.load_path(path)
            self.path, self.dirty = path, False
            self.update_title()
            QTimer.singleShot(0, self.view.fit)
        except (OSError, ValueError, KeyError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Error al abrir",
                f"No se pudo leer el archivo:\n{error}")

    def save_file(self):
        if self.path is None:
            return self.save_file_as()
        return self.write(self.path)

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar autómata", "automata.json", "JSON (*.json)")
        return self.write(path) if path else False

    def write(self, path):
        try:
            self.controller.save_path(path)
        except OSError as error:
            QMessageBox.critical(self, "Error al guardar", str(error))
            return False
        self.path, self.dirty = path, False
        self.update_title()
        self.statusBar().showMessage(f"Guardado en {path}")
        return True

    def closeEvent(self, event):
        event.accept() if self.confirm_discard() else event.ignore()
