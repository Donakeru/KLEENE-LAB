#!/usr/bin/env python3
"""
Teorema de Kleene, parte I: expresión regular -> AFN-λ.

La función pública ``regex_to_automaton`` devuelve directamente un objeto
``Automata`` del modelo. La serialización JSON pertenece exclusivamente a la
capa de persistencia del controlador.

Construcción recursiva:
  - Casos base: ∅, λ, a
  - Unión: un estado inicial nuevo con una λ hacia cada rama
  - Concatenación: λ desde cada final izquierdo al inicio derecho
  - Clausura: estado inicial nuevo, también final, y retornos mediante λ.
    Casos especiales (como en el texto):
      * a*        -> un solo estado inicial y final con un bucle a
      * (R1∪R2)*  -> el inicial de la unión sirve también de nodo de la
                     clausura (sin estado λ intermedio)

Sintaxis:
  unión          : | o ∪
  concatenación  : implícita (ab = a·b)
  clausura       : *
  agrupación     : ( )
  vacío / lambda : ∅ / λ (también se acepta ε)
  símbolos       : cualquier otro carácter
"""

from src.model import Automata


class ErrorSintaxis(ValueError):
    """Error producido por una expresión regular inválida."""


LAMBDA = "λ"  # símbolo canónico de las transiciones lambda

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
        self.es_union = False       # True si su inicial es el nodo nuevo de una unión

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
    def union(self, ramas):
        """Unión de n >= 2 autómatas: un único estado inicial nuevo con una
        transición λ hacia el inicial de cada rama (una bifurcación por elemento)."""
        m = self._nuevo()
        for r in ramas:
            _fusionar(m, r, None)
        q0 = self._q()
        finales = []
        for r in ramas:
            m.agregar(q0, LAMBDA, r.inicial)
            finales += r.finales
        m.inicial = q0
        m.finales = finales
        m.es_union = True
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

        # Clausura de una unión, (R1 ∪ ... ∪ Rn)*: el inicial de la unión no tiene
        # transiciones entrantes, así que sirve también como nodo de la clausura
        # (final, con λ de regreso desde los finales). Evita un estado λ intermedio.
        if m1.es_union:
            m = self._nuevo()
            _fusionar(m, m1, None)
            q0 = m1.inicial
            for f in m1.finales:
                m.agregar(f, LAMBDA, q0)
            m.inicial = q0
            m.finales = m1.finales + [q0]
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
            raise ErrorSintaxis("La expresión regular está vacía (usa λ o ∅).")
        m = self._expr()
        if self._peek() is not None:
            raise ErrorSintaxis(f"Carácter inesperado '{self._peek()}' en la posición {self.i}.")
        return m

    def _expr(self):
        ramas = [self._term()]
        while self._peek() in UNION:
            self._next()
            ramas.append(self._term())
        return ramas[0] if len(ramas) == 1 else self.c.union(ramas)

    def _term(self):
        if self._peek() is None or self._peek() in UNION or self._peek() == ")":
            raise ErrorSintaxis(f"Se esperaba una subexpresión en la posición {self.i}.")
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
                raise ErrorSintaxis("Falta cerrar un paréntesis.")
            return m
        if ch in LAMBDA_CHARS:
            return self.c.lambda_()
        if ch == VACIO:
            return self.c.vacio()
        if ch is None or ch in RESERVADOS:
            raise ErrorSintaxis(f"Símbolo inesperado '{ch}' en la posición {self.i - 1}.")
        if ch not in self.alfabeto:
            self.alfabeto.append(ch)
        return self.c.simbolo(ch)


# ---------------------------------------------------------------------------
# Distribución gráfica de estados
# ---------------------------------------------------------------------------
def _layout(m, dx=200, dy=150, x0=100, y0=100):
    """Distribución por capas (estilo Graphviz) en Python puro, sin dependencias:
      1) Capa de cada estado = camino más largo desde el inicial (las aristas de
         retorno de los bucles/clausuras se ignoran para esto).
      2) Orden dentro de cada capa para reducir cruces (heurística del baricentro).
         Las aristas largas se parten con nodos ficticios para que no atraviesen estados.
      3) Coordenada y: cada estado se acerca al promedio de sus vecinos sin solaparse
         (regresión isotónica), así las cadenas quedan rectas y las bifurcaciones centradas.
    Columna = capa (x), fila = posición en la capa (y).
    """
    n = m.n
    succ = {q: [] for q in range(n)}
    for (o, _), ds in sorted(m.trans.items()):
        for d in ds:
            if d != o and d not in succ[o]:
                succ[o].append(d)

    # --- 1) DFS para detectar aristas de retorno y luego capas por camino más largo
    visit, orden, back = {m.inicial: 1}, [m.inicial], set()
    pila = [(m.inicial, iter(succ[m.inicial]))]
    while pila:
        u, it = pila[-1]
        for v in it:
            if v not in visit:
                visit[v] = 1
                orden.append(v)
                pila.append((v, iter(succ[v])))
                break
            elif visit[v] == 1:
                back.add((u, v))
        else:
            visit[u] = 2
            pila.pop()

    indeg = {q: 0 for q in orden}
    for u in orden:
        for v in succ[u]:
            if (u, v) not in back:
                indeg[v] += 1
    capa = {q: 0 for q in orden}
    cola = [q for q in orden if indeg[q] == 0]
    while cola:
        u = cola.pop(0)
        for v in succ[u]:
            if (u, v) in back:
                continue
            capa[v] = max(capa[v], capa[u] + 1)
            indeg[v] -= 1
            if indeg[v] == 0:
                cola.append(v)
    maxr = max(capa.values())
    for q in range(n):                      # estados inalcanzables (p. ej. el final de ∅)
        capa.setdefault(q, maxr)

    # --- grafo expandido con nodos ficticios para las aristas que saltan capas
    hijos, padres, k = {}, {}, 0
    for u in orden:
        for v in succ[u]:
            if (u, v) in back:
                continue
            cadena = [u]
            for r in range(capa[u] + 1, capa[v]):
                f = ("d", k)
                k += 1
                capa[f] = r
                cadena.append(f)
            cadena.append(v)
            for a, b in zip(cadena, cadena[1:]):
                hijos.setdefault(a, []).append(b)
                padres.setdefault(b, []).append(a)

    # --- 2) orden inicial (DFS) y reducción de cruces
    idx, pila = {}, [m.inicial]
    while pila:
        u = pila.pop()
        if u in idx:
            continue
        idx[u] = len(idx)
        pila.extend(reversed(hijos.get(u, [])))
    for x in capa:
        idx.setdefault(x, len(idx))
    capas = [sorted((x for x in capa if capa[x] == l), key=idx.get) for l in range(maxr + 1)]

    def cruces(cs):
        pos = {x: i for L in cs for i, x in enumerate(L)}
        total = 0
        for l in range(len(cs) - 1):
            ar = [(pos[a], pos[b]) for a in cs[l] for b in hijos.get(a, [])]
            for i in range(len(ar)):
                for j in range(i + 1, len(ar)):
                    if (ar[i][0] - ar[j][0]) * (ar[i][1] - ar[j][1]) < 0:
                        total += 1
        return total

    mejor, mejor_c = [list(L) for L in capas], cruces(capas)
    for _ in range(12):
        for l in range(1, maxr + 1):
            pos = {x: i for i, x in enumerate(capas[l - 1])}
            act = {x: i for i, x in enumerate(capas[l])}
            capas[l].sort(key=lambda x: sum(pos[p] for p in padres[x]) / len(padres[x])
                          if x in padres else act[x])
        for l in range(maxr - 1, -1, -1):
            pos = {x: i for i, x in enumerate(capas[l + 1])}
            act = {x: i for i, x in enumerate(capas[l])}
            capas[l].sort(key=lambda x: sum(pos[h] for h in hijos[x]) / len(hijos[x])
                          if x in hijos else act[x])
        c = cruces(capas)
        if c < mejor_c:
            mejor, mejor_c = [list(L) for L in capas], c
    capas = mejor

    # --- 3) coordenada y: cerca del promedio de los vecinos, sin solapar (PAV)
    y = {x: i * dy for L in capas for i, x in enumerate(L)}

    def acomodar(L, deseado):
        d = [deseado[i] - i * dy for i in range(len(L))]
        bloques = []
        for v in d:
            bloques.append([v, 1])
            while len(bloques) > 1 and bloques[-2][0] / bloques[-2][1] > bloques[-1][0] / bloques[-1][1]:
                s, c = bloques.pop()
                bloques[-1][0] += s
                bloques[-1][1] += c
        z = []
        for s, c in bloques:
            z += [s / c] * c
        for i, x in enumerate(L):
            y[x] = z[i] + i * dy

    def deseado(x):
        vec = padres.get(x, []) + hijos.get(x, [])
        return sum(y[v] for v in vec) / len(vec) if vec else y[x]

    for _ in range(10):
        for l in list(range(1, maxr + 1)) + list(range(maxr - 1, -1, -1)):
            acomodar(capas[l], [deseado(x) for x in capas[l]])

    ymin = min(y[q] for q in range(n))
    return {q: (int(round(x0 + dx * capa[q])), int(round(y0 + y[q] - ymin))) for q in range(n)}


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


def to_automata(m, alfabeto):
    """Convierte la representación interna directamente en ``Automata``."""
    position = _layout(m)
    name = lambda state: f"q{state}"
    automaton = Automata()
    automaton.alfabeto = list(alfabeto)
    for state in range(m.n):
        x, y = position[state]
        automaton.estados[name(state)] = [float(x), float(y)]
    automaton.estado_inicial = name(m.inicial)
    automaton.estados_finales = [name(final)
                                 for final in sorted(set(m.finales))]
    for (origin, symbol), destinations in m.trans.items():
        for destination in destinations:
            automaton.add_transition(
                name(origin), symbol, name(destination))
    return automaton


def regex_to_automaton(expresion):
    """Construye y devuelve directamente un ``Automata`` del modelo."""
    constructor = Constructor()
    parser = Parser(expresion, constructor)
    automaton = compactar(parser.parse())
    return to_automata(automaton, parser.alfabeto)


def acepta(automata, cadena):
    """Compatibilidad para simular un objeto ``Automata`` del modelo."""
    return automata.acepta(cadena)