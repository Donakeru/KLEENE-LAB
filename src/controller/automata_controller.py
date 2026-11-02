"""Controlador de casos de uso del editor de autómatas."""

import json

from PyQt6.QtCore import QObject, pyqtSignal

from src.algorithms.regex_tools import automata_a_regex
from src.algorithms.re_to_af import regex_to_automaton
from src.model import Automata


class AutomataController(QObject):
    """Coordina la vista con el modelo y los algoritmos del dominio.

    La vista puede consultar ``model`` para representar el estado actual, pero
    las mutaciones deben pasar por los métodos de este controlador.
    """

    model_changed = pyqtSignal(object)
    modified = pyqtSignal()
    status = pyqtSignal(str)

    def __init__(self, model=None):
        super().__init__()
        self.model = model or Automata()

    # --- modelo y persistencia --------------------------------------------
    def replace_model(self, model, modified=False):
        self.model = model
        self.model_changed.emit(self.model)
        if modified:
            self.modified.emit()

    def new_model(self):
        self.replace_model(Automata())

    def load_path(self, path):
        with open(path, encoding="utf-8") as file:
            model = Automata.from_dict(json.load(file))
        self.replace_model(model)

    def save_path(self, path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.model.to_dict(), file,
                      ensure_ascii=False, indent=2)

    # --- estados -----------------------------------------------------------
    def move_state(self, sid, x, y):
        if sid not in self.model.estados:
            return False
        self.model.estados[sid] = [x, y]
        self.modified.emit()
        return True

    def next_state_id(self):
        return self.model.next_id()

    def add_state(self, sid, x, y):
        self.model.add_state(sid, x, y)
        self._changed()

    def remove_state(self, sid):
        self.model.remove_state(sid)
        self._changed()

    def rename_state(self, old, new):
        if not self.model.rename_state(old, new):
            return False
        self._changed()
        return True

    def set_initial(self, sid, checked):
        self.model.estado_inicial = sid if checked else None
        self._changed()

    def toggle_initial(self, sid):
        self.model.toggle_initial(sid)
        self._changed()

    def set_final(self, sid, checked):
        if checked and sid not in self.model.estados_finales:
            self.model.estados_finales.append(sid)
        elif not checked and sid in self.model.estados_finales:
            self.model.estados_finales.remove(sid)
        self._changed()

    def toggle_final(self, sid):
        self.model.toggle_final(sid)
        self._changed()

    # --- transiciones y alfabeto ------------------------------------------
    def add_transition(self, origin, symbol, destination):
        added = self.model.add_transition(origin, symbol, destination)
        if added:
            self._changed()
        return added

    def remove_transition(self, origin, symbol, destination):
        self.model.remove_transition(origin, symbol, destination)
        self._changed()

    def remove_transitions(self, transitions):
        for origin, symbol, destination in transitions:
            self.model.remove_transition(origin, symbol, destination)
        self._changed()

    def remove_states(self, states):
        for sid in states:
            self.model.remove_state(sid)
        self._changed()

    def transitions_using_outside(self, alphabet):
        return self.model.transitions_using_outside(alphabet)

    def set_alphabet(self, alphabet):
        self.model.set_alfabeto(alphabet)
        self._changed()

    # --- expresiones regulares --------------------------------------------
    def regex_to_automaton(self, expression):
        return regex_to_automaton(expression)

    def automaton_to_regex(self):
        return automata_a_regex(self.model)

    def _changed(self):
        self.model_changed.emit(self.model)
        self.modified.emit()
