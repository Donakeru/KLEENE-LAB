"""Constantes y datos iniciales de la interfaz gráfica."""

from PyQt6.QtGui import QColor


R = 28
DARK = QColor("#333333")
SELECTED = QColor("#1a73e8")
PENDING = QColor("#e8710a")


class Mode:
    """Modos de interacción de la escena."""

    SELECT, PAN, STATE, TRANS, DELETE = range(5)


HINTS = {
    Mode.SELECT: "Seleccionar: arrastra estados, doble clic en vacío crea un estado, "
                 "doble clic en un estado lo renombra, clic derecho para más opciones. "
                 "Botón central: mover la vista.",
    Mode.PAN: "Mover vista: arrastra con el botón izquierdo para desplazarte por el espacio.",
    Mode.STATE: "Agregar estado: haz clic en una zona vacía.",
    Mode.TRANS: "Agregar transición: clic en el origen y luego en el destino "
                "(el mismo estado crea un lazo). Esc cancela.",
    Mode.DELETE: "Eliminar: haz clic sobre un estado o una transición.",
}


EJEMPLO = {
    "type": "Automata",
    "alfabeto": ["a", "b"],
    "estado_inicial": "q00",
    "estados_finales": ["q00"],
    "estados": [
        {"id": "q00", "x": 100, "y": 150},
        {"id": "q10", "x": 300, "y": 150},
        {"id": "q01", "x": 100, "y": 300},
        {"id": "q11", "x": 300, "y": 300},
    ],
    "transiciones": [
        {"origen": "q00", "simbolo": "a", "destinos": ["q10"]},
        {"origen": "q00", "simbolo": "b", "destinos": ["q01"]},
    ],
}
