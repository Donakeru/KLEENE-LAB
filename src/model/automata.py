"""Modelo de datos del autómata (sin dependencias de Qt).

Formato JSON:
{
  "type": "Automata",
  "alfabeto": ["a", "b"],
  "estado_inicial": "q00",
  "estados_finales": ["q00"],
  "estados": [{"id": "q00", "x": 100, "y": 150}, ...],
  "transiciones": [{"origen": "q00", "simbolo": "a", "destinos": ["q10"]}, ...]
}

Las transiciones lambda usan el símbolo LAMBDA ("λ"). Lambda nunca forma
parte del alfabeto. La notación anterior "ε" se acepta únicamente al abrir
archivos antiguos y se normaliza inmediatamente a "λ".
"""

LAMBDA = "λ"
# Alias de compatibilidad para código externo que importaba EPS.
EPS = LAMBDA
_LEGACY_LAMBDA = "ε"
_LAMBDA_SYMBOLS = frozenset((LAMBDA, _LEGACY_LAMBDA))


def normalizar_simbolo(simbolo):
    """Devuelve la representación canónica de un símbolo de transición."""
    return LAMBDA if simbolo in _LAMBDA_SYMBOLS else simbolo


class Automata:
    def __init__(self):
        self.alfabeto = []
        self.estado_inicial = None
        self.estados_finales = []
        self.estados = {}  # id -> [x, y]
        self.trans = {}    # (origen, simbolo) -> [destinos]

    # --- (de)serialización -------------------------------------------------
    @classmethod
    def from_dict(cls, d):
        a = cls()
        alphabet = (normalizar_simbolo(symbol)
                    for symbol in d.get("alfabeto", []))
        a.alfabeto = [symbol for symbol in dict.fromkeys(alphabet)
                      if symbol != LAMBDA]
        for state in d.get("estados", []):
            a.estados[str(state["id"])] = [
                float(state.get("x", 0)), float(state.get("y", 0))]
        initial = d.get("estado_inicial")
        a.estado_inicial = initial if initial in a.estados else None
        a.estados_finales = [
            state for state in dict.fromkeys(d.get("estados_finales", []))
            if state in a.estados
        ]
        for transition in d.get("transiciones", []):
            origin = transition["origen"]
            symbol = normalizar_simbolo(transition["simbolo"])
            if origin not in a.estados:
                continue
            if symbol != LAMBDA and symbol not in a.alfabeto:
                a.alfabeto.append(symbol)
            for destination in transition.get("destinos", []):
                if destination in a.estados:
                    a.add_transition(origin, symbol, destination)
        return a

    def to_dict(self):
        transitions = []
        for (origin, symbol), destinations in self.trans.items():
            transitions.append({
                "origen": origin,
                "simbolo": normalizar_simbolo(symbol),
                "destinos": list(destinations),
            })
        return {
            "type": "Automata",
            "alfabeto": [normalizar_simbolo(symbol)
                         for symbol in self.alfabeto
                         if normalizar_simbolo(symbol) != LAMBDA],
            "estado_inicial": self.estado_inicial,
            "estados_finales": list(self.estados_finales),
            "estados": [{"id": state_id, "x": round(x), "y": round(y)}
                        for state_id, (x, y) in self.estados.items()],
            "transiciones": transitions,
        }

    # --- estados -----------------------------------------------------------
    def next_id(self):
        index = 0
        while f"q{index}" in self.estados:
            index += 1
        return f"q{index}"

    def add_state(self, sid, x, y):
        self.estados[sid] = [x, y]
        if self.estado_inicial is None:
            self.estado_inicial = sid

    def remove_state(self, sid):
        self.estados.pop(sid, None)
        if self.estado_inicial == sid:
            self.estado_inicial = None
        self.estados_finales = [state for state in self.estados_finales
                                if state != sid]
        new_transitions = {}
        for (origin, symbol), destinations in self.trans.items():
            if origin == sid:
                continue
            destinations = [destination for destination in destinations
                            if destination != sid]
            if destinations:
                new_transitions[(origin, symbol)] = destinations
        self.trans = new_transitions

    def rename_state(self, old, new):
        if new in self.estados or old not in self.estados:
            return False
        self.estados = {(new if state == old else state): position
                        for state, position in self.estados.items()}
        if self.estado_inicial == old:
            self.estado_inicial = new
        self.estados_finales = [new if state == old else state
                                for state in self.estados_finales]
        self.trans = {
            (new if origin == old else origin, symbol):
            [new if destination == old else destination
             for destination in destinations]
            for (origin, symbol), destinations in self.trans.items()
        }
        return True

    def toggle_initial(self, sid):
        self.estado_inicial = None if self.estado_inicial == sid else sid

    def toggle_final(self, sid):
        if sid in self.estados_finales:
            self.estados_finales.remove(sid)
        else:
            self.estados_finales.append(sid)

    # --- transiciones ------------------------------------------------------
    def add_transition(self, origin, symbol, destination):
        symbol = normalizar_simbolo(symbol)
        destinations = self.trans.setdefault((origin, symbol), [])
        if destination in destinations:
            return False
        destinations.append(destination)
        return True

    def remove_transition(self, origin, symbol, destination):
        symbol = normalizar_simbolo(symbol)
        destinations = self.trans.get((origin, symbol))
        if destinations and destination in destinations:
            destinations.remove(destination)
            if not destinations:
                del self.trans[(origin, symbol)]

    def delta(self):
        """Devuelve la función de transición incluyendo las transiciones λ."""
        output = {state: [] for state in self.estados}
        for (origin, symbol), destinations in self.trans.items():
            for destination in destinations:
                output[origin].append((normalizar_simbolo(symbol), destination))
        return output

    # --- alfabeto ----------------------------------------------------------
    def transitions_using_outside(self, alphabet):
        alphabet = {normalizar_simbolo(symbol) for symbol in alphabet}
        return sum(
            len(destinations)
            for (_, symbol), destinations in self.trans.items()
            if normalizar_simbolo(symbol) != LAMBDA
            and normalizar_simbolo(symbol) not in alphabet
        )

    def set_alfabeto(self, alphabet):
        self.alfabeto = list(dict.fromkeys(
            normalizar_simbolo(symbol) for symbol in alphabet
            if normalizar_simbolo(symbol) != LAMBDA))
        new_transitions = {}
        for (origin, symbol), destinations in self.trans.items():
            symbol = normalizar_simbolo(symbol)
            if symbol == LAMBDA or symbol in self.alfabeto:
                key = (origin, symbol)
                current = new_transitions.setdefault(key, [])
                for destination in destinations:
                    if destination not in current:
                        current.append(destination)
        self.trans = new_transitions

    # --- simulación --------------------------------------------------------
    def cierre_lambda(self, states):
        closure = set(states)
        stack = list(closure)
        while stack:
            state = stack.pop()
            for destination in self.trans.get((state, LAMBDA), []):
                if destination not in closure:
                    closure.add(destination)
                    stack.append(destination)
        return closure

    def mover(self, states, symbol):
        result = set()
        for state in states:
            result.update(self.trans.get(
                (state, normalizar_simbolo(symbol)), []))
        return result

    def acepta(self, cadena):
        """True si el autómata acepta la cadena."""
        if self.estado_inicial is None:
            return False
        current = self.cierre_lambda({self.estado_inicial})
        for character in cadena:
            current = self.cierre_lambda(self.mover(current, character))
        return bool(current & set(self.estados_finales))
