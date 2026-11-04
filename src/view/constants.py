"""Constantes y datos iniciales de la interfaz gráfica."""

from PyQt6.QtGui import QColor


R = 28
FONT = "Segoe UI"

# Paleta de la interfaz (cadenas para hojas de estilo): papel, tinta y verde.
ACCENT = "#2f6b4f"          # verde bosque
ACCENT_HOVER = "#255a41"
ACCENT_SOFT = "#ecf3ee"
ACCENT_LINE = "#bcd3c4"
ACCENT_PRESSED = "#dbe9df"
SURFACE = "#f5f2ec"         # papel
PANEL = "#fdfbf7"
BORDER = "#e2dbcf"
TEXT = "#2b2722"            # tinta
TEXT_MUTED = "#7a7166"
TEXT_DISABLED = "#b0a89c"
SCROLL = "#d3cbbd"
SCROLL_HOVER = "#a99f90"

# Colores del lienzo.
DARK = QColor("#3a342d")
SELECTED = QColor(ACCENT)
PENDING = QColor("#c47a12")       # ámbar
INITIAL = QColor("#b4532a")       # terracota
STATE_FILL = QColor("#ffffff")
SELECTED_FILL = QColor(ACCENT_SOFT)
PENDING_FILL = QColor("#fbf1df")
FINAL_FILL = QColor("#f7eee2")
CANVAS_BG = QColor("#fbf9f5")
CANVAS_DOT = QColor("#d9d1c4")


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
