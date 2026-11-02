"""Puntos de extensión para conversiones entre ER y autómatas.

La implementación de los algoritmos pertenece a esta capa de dominio y queda
intencionalmente pendiente para que pueda incorporarse según la teoría del
curso. La notación canónica para la cadena vacía es ``λ``.
"""


class ErrorSintaxis(ValueError):
    """Error producido por una expresión regular inválida."""


def regex_a_automata(texto):
    """Convierte una expresión regular en un autómata.

    Este método es el punto de extensión para la implementación de la
    construcción de ER a AF.
    """
    raise NotImplementedError("regex_a_automata: pendiente de implementar")


def automata_a_regex(automata):
    """Convierte un autómata en una expresión regular.

    Este método es el punto de extensión para la implementación del algoritmo
    de autómata a ER, por ejemplo mediante el lema de Arden.
    """
    raise NotImplementedError("automata_a_regex: pendiente de implementar")
