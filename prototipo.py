#!/usr/bin/env python3
"""
Teorema de Kleene, parte I: expresión regular -> AFN-λ.

Construcción recursiva (por inducción sobre la estructura de R):
  - Casos base: ∅, λ, a
  - Unión (R ∪ S): estado inicial nuevo con λ hacia los iniciales de M1 y M2;
                   finales = finales(M1) ∪ finales(M2)
  - Concatenación (RS): λ desde cada final de M1 al inicial de M2;
                        finales = finales(M2)
  - Clausura de un símbolo (a*): un solo estado inicial y final con bucle a (simplificación de 2.9)
  - Clausura (R*) general: estado inicial nuevo (también final) con λ hacia el inicial
                   de M1; λ desde cada final de M1 de regreso al inicial nuevo;
                   finales = finales(M1) ∪ {inicial nuevo}

Sintaxis de la expresión regular de entrada:
  unión          : |  o  ∪
  concatenación  : implícita (ab = a·b)
  clausura       : *
  agrupación     : ( )
  vacío / lambda : ∅  /  λ  (también se acepta ε)
  símbolos       : cualquier otro carácter (a, b, c, 0, 1, ...)

Uso:
  python regex_a_afnlambda.py "a*(ab|ba)*|a(b|a*)"
  python regex_a_afnlambda.py "a*(ab∪ba)*" -o salida.json
"""

import argparse
import json
import sys

LAMBDA = "λ"  # símbolo usado en el JSON para las transiciones λ

UNION = {"|", "∪"}
LAMBDA_CHARS = {"λ", "ε"}
VACIO = "∅"
RESERVADOS = UNION | LAMBDA_CHARS | {VACIO, "(", ")", "*"}


# ---------------------------------------------------------------------------
# Representación del autómata
# ---------------------------------------------------------------------------
class AFNLambda:
    """AFN-λ con un único estado inicial y varios finales."""

    def __init__(self):
        self.n = 0                  # contador de estados
        self.trans = {}             # (origen, simbolo) -> lista de destinos
        self.inicial = None
        self.finales = []           # lista de estados finales
        self.simbolo_basico = None  # 'a' si es el autómata básico q0 -a-> q1

    def nuevo_estado(self):
        q = self.n
        self.n += 1
        return q

    def agregar(self, origen, simbolo, destino):
        destinos = self.trans.setdefault((origen, simbolo), [])
        if destino not in destinos:
            destinos.append(destino)


def _fusionar(m, a, b):
    """Copia los estados/transiciones de a y b dentro de m (ya con ids únicos)."""
    for aut in (a, b):
        if aut is None:
            continue
        for (o, s), ds in aut.trans.items():
            for d in ds:
                m.agregar(o, s, d)


# ---------------------------------------------------------------------------
# Construcciones (una por cada caso del teorema)
# ---------------------------------------------------------------------------
class Constructor:
    """Comparte un contador global para que los ids de estado no se repitan."""

    def __init__(self):
        self.contador = 0

    def _q(self):
        q = self.contador
        self.contador += 1
        return q

    def _nuevo(self):
        m = AFNLambda()
        return m

    # --- casos base ---
    def vacio(self):
        m = self._nuevo()
        q0, q1 = self._q(), self._q()
        m.inicial, m.finales = q0, [q1]          # sin transiciones
        return m

    def lambda_(self):
        m = self._nuevo()
        q0 = self._q()
        m.inicial, m.finales = q0, [q0]
        return m

    def simbolo(self, a):
        m = self._nuevo()
        q0, q1 = self._q(), self._q()
        m.agregar(q0, a, q1)
        m.inicial, m.finales = q0, [q1]
        m.simbolo_basico = a
        return m

    # --- paso inductivo ---
    def union(self, m1, m2):
        m = self._nuevo()
        _fusionar(m, m1, m2)
        q0 = self._q()
        m.agregar(q0, LAMBDA, m1.inicial)
        m.agregar(q0, LAMBDA, m2.inicial)
        m.inicial = q0
        m.finales = m1.finales + m2.finales
        return m

    def concatenacion(self, m1, m2):
        m = self._nuevo()
        _fusionar(m, m1, m2)
        for f in m1.finales:
            m.agregar(f, LAMBDA, m2.inicial)
        m.inicial = m1.inicial
        m.finales = list(m2.finales)
        return m

    def clausura(self, m1):
        # Simplificación del texto (sección 2.9): a* = un único estado,
        # inicial y final, con un bucle etiquetado a.
        if m1.simbolo_basico is not None:
            m = self._nuevo()
            q = m1.inicial
            m.agregar(q, m1.simbolo_basico, q)
            m.inicial, m.finales = q, [q]
            return m

        # Construcción general
        m = self._nuevo()
        _fusionar(m, m1, None)
        q0 = self._q()
        m.agregar(q0, LAMBDA, m1.inicial)
        for f in m1.finales:
            m.agregar(f, LAMBDA, q0)
        m.inicial = q0
        m.finales = m1.finales + [q0]
        return m


# ---------------------------------------------------------------------------
# Parser recursivo descendente (construye el autómata directamente)
#   expr   := term (UNION term)*
#   term   := factor+
#   factor := atomo '*'*
#   atomo  := '(' expr ')' | λ | ∅ | símbolo
# ---------------------------------------------------------------------------
class Parser:
    def __init__(self, texto, constructor):
        self.t = [c for c in texto if not c.isspace()]
        self.i = 0
        self.c = constructor
        self.alfabeto = []

    def _peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def _next(self):
        ch = self._peek()
        self.i += 1
        return ch

    def parse(self):
        if not self.t:
            raise ValueError("La expresión regular está vacía (usa λ o ∅).")
        m = self._expr()
        if self._peek() is not None:
            raise ValueError(f"Carácter inesperado '{self._peek()}' en la posición {self.i}.")
        return m

    def _expr(self):
        m = self._term()
        while self._peek() in UNION:
            self._next()
            m = self.c.union(m, self._term())
        return m

    def _term(self):
        if self._peek() is None or self._peek() in UNION or self._peek() == ")":
            raise ValueError(f"Se esperaba una subexpresión en la posición {self.i}.")
        m = self._factor()
        while self._peek() is not None and self._peek() not in UNION and self._peek() != ")":
            m = self.c.concatenacion(m, self._factor())
        return m

    def _factor(self):
        m = self._atomo()
        while self._peek() == "*":
            self._next()
            m = self.c.clausura(m)
        return m

    def _atomo(self):
        ch = self._next()
        if ch == "(":
            m = self._expr()
            if self._next() != ")":
                raise ValueError("Falta cerrar un paréntesis.")
            return m
        if ch in LAMBDA_CHARS:
            return self.c.lambda_()
        if ch == VACIO:
            return self.c.vacio()
        if ch is None or ch in RESERVADOS:
            raise ValueError(f"Símbolo inesperado '{ch}' en la posición {self.i - 1}.")
        if ch not in self.alfabeto:
            self.alfabeto.append(ch)
        return self.c.simbolo(ch)


# ---------------------------------------------------------------------------
# Exportación al formato JSON pedido
# ---------------------------------------------------------------------------
def _layout(m, dx=200, dy=150, x0=100, y0=150):
    """Posiciones (x, y): columna = distancia desde el inicial (BFS), fila = orden dentro de la columna."""
    vecinos = {}
    for (o, _), ds in m.trans.items():
        vecinos.setdefault(o, []).extend(ds)

    nivel = {m.inicial: 0}
    cola = [m.inicial]
    while cola:
        u = cola.pop(0)
        for v in vecinos.get(u, []):
            if v not in nivel:
                nivel[v] = nivel[u] + 1
                cola.append(v)

    # estados no alcanzables (p. ej. el final de ∅) van en la última columna + 1
    maximo = max(nivel.values())
    for q in range(m.n):
        if q not in nivel:
            nivel[q] = maximo + 1

    filas = {}
    pos = {}
    for q in sorted(range(m.n), key=lambda q: (nivel[q], q)):
        fila = filas.get(nivel[q], 0)
        filas[nivel[q]] = fila + 1
        pos[q] = (x0 + dx * nivel[q], y0 + dy * fila)
    return pos


def compactar(m):
    """Renumera los estados usados a 0..n-1 (la simplificación de a* deja huecos)."""
    usados = {m.inicial, *m.finales}
    for (o, _), ds in m.trans.items():
        usados.add(o)
        usados.update(ds)
    nuevo = {q: i for i, q in enumerate(sorted(usados))}

    r = AFNLambda()
    r.n = len(nuevo)
    r.inicial = nuevo[m.inicial]
    r.finales = [nuevo[f] for f in m.finales]
    for (o, s), ds in m.trans.items():
        for d in ds:
            r.agregar(nuevo[o], s, nuevo[d])
    return r


def a_json(m, alfabeto):
    pos = _layout(m)
    nombre = lambda q: f"q{q}"

    estados = [{"id": nombre(q), "x": pos[q][0], "y": pos[q][1]} for q in range(m.n)]
    transiciones = [
        {"origen": nombre(o), "simbolo": s, "destinos": [nombre(d) for d in ds]}
        for (o, s), ds in sorted(m.trans.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    ]
    return {
        "type": "Automata",
        "alfabeto": alfabeto,
        "estado_inicial": nombre(m.inicial),
        "estados_finales": [nombre(f) for f in sorted(set(m.finales))],
        "estados": estados,
        "transiciones": transiciones,
    }


def regex_a_afn_lambda(expresion):
    """Devuelve el AFN-λ equivalente a la expresión regular, como dict listo para json.dumps."""
    c = Constructor()
    p = Parser(expresion, c)
    m = p.parse()
    m = compactar(m)
    return a_json(m, p.alfabeto)


# ---------------------------------------------------------------------------
# Simulación (opcional, sirve para comprobar que L(M) = R)
# ---------------------------------------------------------------------------
def acepta(automata, cadena):
    trans = {}
    for t in automata["transiciones"]:
        trans[(t["origen"], t["simbolo"])] = t["destinos"]

    def clausura_lambda(conjunto):
        pila, res = list(conjunto), set(conjunto)
        while pila:
            u = pila.pop()
            for v in trans.get((u, LAMBDA), []):
                if v not in res:
                    res.add(v)
                    pila.append(v)
        return res

    actuales = clausura_lambda({automata["estado_inicial"]})
    for ch in cadena:
        sig = set()
        for u in actuales:
            sig.update(trans.get((u, ch), []))
        actuales = clausura_lambda(sig)
    return bool(actuales & set(automata["estados_finales"]))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Expresión regular -> AFN-λ (Teorema de Kleene, parte I)")
    ap.add_argument("expresion", help='ej: "a*(ab|ba)*|a(b|a*)"')
    ap.add_argument("-o", "--salida", help="archivo .json de salida (por defecto, stdout)")
    args = ap.parse_args()

    try:
        resultado = regex_a_afn_lambda(args.expresion)
    except ValueError as e:
        sys.exit(f"Error: {e}")

    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(texto + "\n")
        print(f"Guardado en {args.salida}")
    else:
        print(texto)


if __name__ == "__main__":
    main()