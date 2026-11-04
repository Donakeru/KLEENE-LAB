#!/usr/bin/env python3
"""
Teorema de Kleene, parte II: autómata finito -> expresión regular.

Implementa el **lema de Arden** por el método de eliminación de incógnitas
(sustitución), tal como se desarrolla a mano:

Para cada estado ``Aᵢ`` se plantea una ecuación lingüística::

    Aᵢ = ( Σ  xₖ · Aⱼ )  ∪  (λ si Aᵢ es final)

donde ``xₖ`` es el símbolo de cada transición ``Aᵢ --xₖ--> Aⱼ``.

El sistema se resuelve sustituyendo variables unas en otras. Cuando una
variable queda referida a sí misma::

    X = α·X ∪ β        (lema de Arden)   ==>   X = α*·β

La solución de la ecuación del estado inicial es la ER buscada.

Nota sobre ``a*`` frente a ``a+``
---------------------------------
El lema produce la **estrella de Kleene** ``α*`` (que incluye λ):

    X = aX ∪ λ   ==>   X = a*·λ = a*          (contiene la cadena vacía)

En cambio ``a+ = a·a*`` es la clausura positiva (no contiene λ) y aparece
cuando el bucle NO tiene un término independiente que aporte λ, p. ej.:

    X = aX ∪ bY ,  Y = ...   ==>   X = a*·(bY)   →   si de ahí vuelve a X sin
    pasar por un final, la parte recurrente da ``a+`` en lugar de ``a*``.

El álgebra de más abajo distingue ambos: ``Estrella`` representa ``α*`` y el
método ``mas()`` (``α+ = α·α*``) se usa internamente cuando corresponde.
"""

from src.model import LAMBDA, Automata

# Símbolos textuales de la ER resultante.
VACIO = "∅"          # lenguaje vacío
UNION = "∪"          # unión, como en el desarrollo a mano (a∪b)


# ---------------------------------------------------------------------------
# Álgebra de expresiones regulares (AST con simplificación básica)
# ---------------------------------------------------------------------------
class RE:
    """Clase base de los nodos de expresión regular."""

    # Precedencias para parentizar: unión < concatenación < estrella < átomo.
    PREC_UNION = 1
    PREC_CONCAT = 2
    PREC_STAR = 3
    PREC_ATOM = 4

    def prec(self):
        raise NotImplementedError

    def es_vacio(self):
        return False

    def es_lambda(self):
        return False

    def __str__(self):
        return self.render(0)

    def render(self, parent_prec):
        texto = self._texto()
        return f"({texto})" if self.prec() < parent_prec else texto

    def _texto(self):
        raise NotImplementedError


class Vacio(RE):
    """Lenguaje vacío ∅ (elemento absorbente de la concatenación,
    neutro de la unión)."""

    def prec(self):
        return RE.PREC_ATOM

    def es_vacio(self):
        return True

    def _texto(self):
        return VACIO

    def __eq__(self, otro):
        return isinstance(otro, Vacio)

    def __hash__(self):
        return hash("∅")


class Lambda(RE):
    """Cadena vacía λ (elemento neutro de la concatenación)."""

    def prec(self):
        return RE.PREC_ATOM

    def es_lambda(self):
        return True

    def _texto(self):
        return LAMBDA

    def __eq__(self, otro):
        return isinstance(otro, Lambda)

    def __hash__(self):
        return hash("λ")


class Simbolo(RE):
    """Un símbolo del alfabeto."""

    def __init__(self, valor):
        self.valor = valor

    def prec(self):
        return RE.PREC_ATOM

    def _texto(self):
        return self.valor

    def __eq__(self, otro):
        return isinstance(otro, Simbolo) and otro.valor == self.valor

    def __hash__(self):
        return hash(("sym", self.valor))


class Union(RE):
    """Unión de dos o más alternativas (sin repetidos)."""

    def __init__(self, partes):
        self.partes = partes

    def prec(self):
        return RE.PREC_UNION

    def _texto(self):
        return UNION.join(parte.render(RE.PREC_UNION) for parte in self.partes)

    def __eq__(self, otro):
        return isinstance(otro, Union) and otro.partes == self.partes

    def __hash__(self):
        return hash(("union", tuple(self.partes)))


class Concat(RE):
    """Concatenación de dos o más factores."""

    def __init__(self, partes):
        self.partes = partes

    def prec(self):
        return RE.PREC_CONCAT

    def _texto(self):
        return "".join(parte.render(RE.PREC_CONCAT) for parte in self.partes)

    def __eq__(self, otro):
        return isinstance(otro, Concat) and otro.partes == self.partes

    def __hash__(self):
        return hash(("concat", tuple(self.partes)))


class Estrella(RE):
    """Clausura de Kleene α* (incluye λ)."""

    def __init__(self, interno):
        self.interno = interno

    def prec(self):
        return RE.PREC_STAR

    def _texto(self):
        return f"{self.interno.render(RE.PREC_STAR)}*"

    def __eq__(self, otro):
        return isinstance(otro, Estrella) and otro.interno == self.interno

    def __hash__(self):
        return hash(("estrella", self.interno))


class Mas(RE):
    """Clausura positiva α+ = α·α* (NO incluye λ).

    Se distingue de ``Estrella`` tanto en el lenguaje (``α+`` no acepta λ)
    como en el texto. Para evitar colisión con el ``+`` de la unión, se
    renderiza siempre en su forma expandida ``αα*`` (que es inequívoca).
    La distinción conceptual ``a*`` (incluye λ) frente a ``a+ = aa*`` (sin λ)
    queda así reflejada sin ambigüedad en la cadena resultante.
    """

    def __init__(self, interno):
        self.interno = interno

    def prec(self):
        return RE.PREC_CONCAT

    def _texto(self):
        base = self.interno.render(RE.PREC_STAR)
        return f"{base}{base}*"

    def __eq__(self, otro):
        return isinstance(otro, Mas) and otro.interno == self.interno

    def __hash__(self):
        return hash(("mas", self.interno))


# ---------------------------------------------------------------------------
# Constructores con simplificación (mantienen el AST pequeño y legible)
# ---------------------------------------------------------------------------
def vacio():
    return Vacio()


def lamb():
    return Lambda()


def simbolo(valor):
    return Simbolo(valor)


def union(*expresiones):
    """Unión simplificada:
      - ∅ es neutro (se descarta)
      - se aplanan uniones anidadas
      - se eliminan duplicados conservando el orden
    """
    partes = []
    for expresion in expresiones:
        if expresion is None or expresion.es_vacio():
            continue
        if isinstance(expresion, Union):
            partes.extend(expresion.partes)
        else:
            partes.append(expresion)
    unicas = []
    for parte in partes:
        if parte not in unicas:
            unicas.append(parte)
    unicas = _absorber_union(unicas)
    unicas.sort(key=lambda parte: parte.es_lambda())
    if not unicas:
        return vacio()
    if len(unicas) == 1:
        return unicas[0]
    return Union(unicas)


def distribuir(alfa, beta):
    """``α·β`` aplicando la distributiva si β es una unión:
    α(β₁ ∪ β₂) = αβ₁ ∪ αβ₂ (como se hace al sustituir a mano)."""
    if isinstance(beta, Union):
        return union(*(concat(alfa, parte) for parte in beta.partes))
    return concat(alfa, beta)


def _absorber_union(partes):
    """Simplificaciones de la unión que se hacen a mano:
      - α + α*  = α*      (α* ya contiene α)
      - α+ + α* = α*
      - λ + α*  = α*      (α* ya contiene λ)
      - λ + α+  = α*      (λ ∪ αα* = α*)
    """
    estrellas = {p.interno for p in partes if isinstance(p, Estrella)}
    resultado = [p for p in partes
                 if not (p in estrellas
                         or (isinstance(p, Mas) and p.interno in estrellas))]
    if any(p.es_lambda() for p in resultado):
        mases = [p for p in resultado if isinstance(p, Mas)]
        if any(isinstance(p, Estrella) for p in resultado) or mases:
            resultado = [Estrella(p.interno) if isinstance(p, Mas) else p
                         for p in resultado if not p.es_lambda()]
    return resultado


def _sin_lambda(expresion):
    """Devuelve ``α`` si la expresión es ``λ + α`` (o ``α + λ``); si no, None."""
    if isinstance(expresion, Union) and any(p.es_lambda() for p in expresion.partes):
        resto = [p for p in expresion.partes if not p.es_lambda()]
        return resto[0] if len(resto) == 1 else Union(resto)
    return None


def concat(*expresiones):
    """Concatenación simplificada:
      - ∅ es absorbente  (α∅ = ∅α = ∅)
      - λ es neutro       (αλ = λα = α)
      - se aplanan concatenaciones anidadas
      - α*·α = α·α* = α+  (estrella de Kleene · base = clausura positiva)
    """
    partes = []
    for expresion in expresiones:
        if expresion is None:
            continue
        if expresion.es_vacio():
            return vacio()
        if expresion.es_lambda():
            continue
        if isinstance(expresion, Concat):
            partes.extend(expresion.partes)
        else:
            partes.append(expresion)
    partes = _fusionar_estrella_base(partes)
    if not partes:
        return lamb()
    if len(partes) == 1:
        return partes[0]
    return Concat(partes)


def _fusionar_estrella_base(partes):
    """Colapsa factores adyacentes ``α*·α`` o ``α·α*`` en ``α+``.

    Esta es la distinción que se escribe a mano: la estrella de Kleene ``α*``
    (incluye λ) multiplicada por una copia de ``α`` produce la clausura
    positiva ``α+`` (sin λ).
    """
    resultado = []
    for parte in partes:
        if resultado:
            previo = resultado[-1]
            # α* · α*  ->  α*
            if isinstance(previo, Estrella) and parte == previo:
                continue
            # α* · (λ+α)  ->  α*      y      (λ+α) · α*  ->  α*
            if isinstance(previo, Estrella) and _sin_lambda(parte) == previo.interno:
                continue
            if isinstance(parte, Estrella) and _sin_lambda(previo) == parte.interno:
                resultado[-1] = parte
                continue
            # α+ · α*  ->  α+        y      α* · α+  ->  α+
            if isinstance(previo, Mas) and isinstance(parte, Estrella)                     and previo.interno == parte.interno:
                continue
            if isinstance(previo, Estrella) and isinstance(parte, Mas)                     and previo.interno == parte.interno:
                resultado[-1] = parte
                continue
            # α* · α  ->  α+
            if isinstance(previo, Estrella) and previo.interno == parte:
                resultado[-1] = Mas(parte)
                continue
            # α · α*  ->  α+
            if isinstance(parte, Estrella) and parte.interno == previo:
                resultado[-1] = Mas(previo)
                continue
            # α+ · α  ->  α+·α  (se deja; ya no es un simple +)
        resultado.append(parte)
    return resultado


def estrella(expresion):
    """Clausura simplificada:
      - ∅* = λ
      - λ* = λ
      - (α*)* = α*
    """
    if expresion.es_vacio() or expresion.es_lambda():
        return lamb()
    if isinstance(expresion, (Estrella, Mas)):
        return Estrella(expresion.interno)
    if isinstance(expresion, Union):
        # (λ + α)* = α*    y    (α* + β)* = (α + β)*
        partes = [p.interno if isinstance(p, (Estrella, Mas)) else p
                  for p in expresion.partes if not p.es_lambda()]
        interno = union(*partes)
        if interno.es_vacio() or interno.es_lambda():
            return lamb()
        if isinstance(interno, (Estrella, Mas)):
            return Estrella(interno.interno)
        return Estrella(interno)
    return Estrella(expresion)


def mas(expresion):
    """Clausura positiva α+ = α·α* (no incluye λ)."""
    if expresion.es_vacio():
        return vacio()
    if expresion.es_lambda():
        return lamb()
    return Mas(expresion)


# ---------------------------------------------------------------------------
# Lema de Arden sobre el sistema de ecuaciones
# ---------------------------------------------------------------------------
class ArdenSolver:
    """Resuelve el sistema ``Aᵢ = Σ coef(i,j)·Aⱼ ∪ term(i)``.

    - ``coef[i][j]``: ER que etiqueta el paso directo del estado i al j
      (unión de todos los símbolos de las transiciones i→j).
    - ``indep[i]``:   término independiente (λ si i es final, ∅ si no).

    El autómata puede ser no determinista y tener transiciones λ: cada
    transición ``i --x--> j`` aporta el símbolo ``x`` (o λ) al coeficiente
    ``coef[i][j]``.
    """

    def __init__(self, automata):
        self.estados = list(automata.estados.keys())
        self.inicial = automata.estado_inicial
        finales = set(automata.estados_finales)

        # Matriz de coeficientes y vector independiente.
        self.coef = {i: {j: vacio() for j in self.estados}
                     for i in self.estados}
        self.indep = {i: (lamb() if i in finales else vacio())
                      for i in self.estados}

        for (origen, simbolo_trans), destinos in automata.trans.items():
            if origen not in self.coef:
                continue
            etiqueta = lamb() if simbolo_trans == LAMBDA else simbolo(simbolo_trans)
            for destino in destinos:
                if destino in self.coef[origen]:
                    self.coef[origen][destino] = union(
                        self.coef[origen][destino], etiqueta)

    def resolver(self):
        """Elimina incógnitas una a una y devuelve la ER del estado inicial."""
        if self.inicial is None:
            return vacio()

        # Orden de eliminación, como a mano: se empieza por el estado más
        # lejano al inicial y se va sustituyendo hacia atrás (A4 en A3, A3 en
        # A2, ...). El inicial se resuelve al final.
        pendientes = self._orden_eliminacion()

        for x in pendientes:
            self._eliminar(x)

        # Queda una sola ecuación: A_inicial = coef[ini][ini]·A_inicial ∪ indep[ini]
        self._arden_propio(self.inicial)
        return self.indep[self.inicial]

    def _orden_eliminacion(self):
        """Estados (sin el inicial) ordenados del más lejano al más cercano
        al inicial según la distancia en transiciones (BFS). Los empates y
        los estados inalcanzables se resuelven por orden de definición, del
        último al primero."""
        distancia = {self.inicial: 0}
        cola = [self.inicial]
        for actual in cola:
            for destino in self.estados:
                if destino not in distancia and not self.coef[actual][destino].es_vacio():
                    distancia[destino] = distancia[actual] + 1
                    cola.append(destino)
        lejano = len(self.estados) + 1
        posicion = {estado: indice for indice, estado in enumerate(self.estados)}
        resto = [e for e in self.estados if e != self.inicial]
        return sorted(resto, key=lambda e: (-distancia.get(e, lejano), -posicion[e]))

    def _arden_propio(self, x):
        """Aplica el lema de Arden a la ecuación del estado ``x``:
        X = α·X ∪ β  ==>  X = α*·β. Deja ``coef[x][x] = ∅``."""
        alfa = self.coef[x][x]
        if not alfa.es_vacio():
            estrella_alfa = estrella(alfa)
            self.coef[x][x] = vacio()
            self.indep[x] = concat(estrella_alfa, self.indep[x])
            for j in self.estados:
                if j != x:
                    self.coef[x][j] = concat(estrella_alfa, self.coef[x][j])

    def _eliminar(self, x):
        """Resuelve ``x`` con Arden y sustituye su valor en las demás
        ecuaciones (eliminación gaussiana sobre el semianillo de ER)."""
        # 1) Resolver el autobucle de x: x = α*·(resto).
        self._arden_propio(x)

        # 2) Sustituir x en toda ecuación que lo referencie.
        for i in self.estados:
            if i == x:
                continue
            coef_ix = self.coef[i][x]
            if coef_ix.es_vacio():
                continue
            # La ecuación de i tenía ... ∪ coef_ix · X.
            # Reemplazamos X por su expresión resuelta.
            self.coef[i][x] = vacio()
            self.indep[i] = union(self.indep[i],
                                  distribuir(coef_ix, self.indep[x]))
            for j in self.estados:
                if j == x:
                    continue
                aporte = distribuir(coef_ix, self.coef[x][j])
                if not aporte.es_vacio():
                    self.coef[i][j] = union(self.coef[i][j], aporte)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def automaton_to_regex(automata):
    """Devuelve la ER (``str``) equivalente al ``Automata`` dado.

    Usa el lema de Arden. Si el autómata no tiene estado inicial, devuelve ∅.
    Si no tiene estados finales alcanzables, el resultado se simplifica a ∅.
    """
    if not isinstance(automata, Automata):
        automata = Automata.from_dict(automata)
    solver = ArdenSolver(automata)
    resultado = solver.resolver()
    return str(resultado)
