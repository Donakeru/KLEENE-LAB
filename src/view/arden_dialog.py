"""Ventana con el desarrollo paso a paso del lema de Arden."""

from html import escape

from PyQt6.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                             QPushButton, QTextBrowser, QVBoxLayout)

from .constants import ACCENT, ACCENT_SOFT, BORDER, TEXT, TEXT_MUTED


def pasos_a_texto(pasos, expresion):
    """Versión en texto plano (para copiar y pegar en un informe)."""
    lineas = []
    for numero, paso in enumerate(pasos, 1):
        lineas.append(f"Paso {numero}. {paso['titulo']}")
        if paso["nota"]:
            lineas.append(f"  {paso['nota']}")
        for texto, ecuacion, recuadrada, etiqueta in paso["lineas"]:
            if ecuacion is None:
                lineas.append(f"  ▸ {texto}")
                continue
            if texto:
                lineas.append(f"  {texto}:")
            marca = f"   ({etiqueta})" if etiqueta else ""
            cuerpo = f"[ {ecuacion} ]" if recuadrada else ecuacion
            lineas.append(f"      {cuerpo}{marca}")
        lineas.append("")
    lineas.append(f"Expresión regular: {expresion}")
    return "\n".join(lineas)


def pasos_a_html(pasos, expresion):
    """Desarrollo con formato: títulos, ecuaciones numeradas y recuadros."""
    partes = [f"""
<div style="color:{TEXT}; font-family:'Segoe UI'; font-size:10.5pt;">
<p style="font-size:9.5pt; color:{TEXT_MUTED};">
Se plantea una ecuación por estado y se eliminan las incógnitas desde el
estado más lejano al inicial, aplicando el lema de Arden
(<i>X = αX ∪ β ⟹ X = α*β</i>) cuando una variable depende de sí misma.</p>
"""]
    for numero, paso in enumerate(pasos, 1):
        partes.append(
            f"<h3 style='color:{ACCENT}; margin-top:16px; margin-bottom:4px;'>"
            f"Paso {numero}. {escape(paso['titulo'])}</h3>")
        if paso["nota"]:
            partes.append(f"<p style='color:{TEXT_MUTED}; margin:0 0 6px 0;'>"
                          f"{escape(paso['nota'])}</p>")
        for texto, ecuacion, recuadrada, etiqueta in paso["lineas"]:
            if ecuacion is None:
                partes.append(f"<p style='margin:10px 0 2px 0;'><b>▸ {escape(texto)}</b></p>")
                continue
            if texto:
                partes.append(f"<p style='color:{TEXT_MUTED}; margin:4px 0 0 18px;'>"
                              f"{escape(texto)}:</p>")
            marca = (f"<td width='60' align='right' style='color:{TEXT_MUTED};'>"
                     f"({etiqueta})</td>" if etiqueta else "<td width='60'></td>")
            estilo = "font-family:'Cambria Math','Cambria',serif; font-size:13pt;"
            if recuadrada:
                celda = (f"<table cellpadding='6' cellspacing='0' border='1' "
                         f"style='border-color:{ACCENT}; border-style:solid;' "
                         f"bgcolor='{ACCENT_SOFT}'><tr><td style=\"{estilo}\">"
                         f"{escape(ecuacion)}</td></tr></table>")
            else:
                celda = f"<span style=\"{estilo}\">{escape(ecuacion)}</span>"
            partes.append(f"<table width='100%' cellpadding='2'><tr>"
                          f"<td width='30'></td><td align='center'>{celda}</td>"
                          f"{marca}</tr></table>")
    partes.append(f"<hr style='color:{BORDER};'/><p><b>Expresión regular:</b> "
                  f"<span style=\"font-family:'Cambria Math','Cambria',serif; "
                  f"font-size:13pt;\">{escape(expresion)}</span></p></div>")
    return "".join(partes)


class ArdenStepsDialog(QDialog):
    """Muestra cómo se llegó a la ER, con opción de copiar el desarrollo."""

    def __init__(self, parent, pasos, expresion):
        super().__init__(parent)
        self.setWindowTitle("Lema de Arden — paso a paso")
        self.resize(760, 680)
        self._texto = pasos_a_texto(pasos, expresion)

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenLinks(False)
        browser.setHtml(pasos_a_html(pasos, expresion))
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        copy_button = QPushButton("Copiar desarrollo")
        copy_button.clicked.connect(self._copiar)
        buttons.addButton(copy_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _copiar(self):
        QApplication.clipboard().setText(self._texto)
        self.setWindowTitle("Lema de Arden — paso a paso (copiado)")
