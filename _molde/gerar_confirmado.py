"""Gera cartas/confirmado.html (inscrição confirmada) com a casca de sobre.html.

Uso: python3 _molde/gerar_confirmado.py
Rodar de novo se o menu ou o rodapé de sobre.html mudarem. Página noindex, destino
do POST de confirmação do backend (/cartas/confirmar). Texto aprovado em 25/09/2026
(compliance_audit d00c641c).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_carta as gc  # noqa: E402

TITULO = "Inscrição confirmada · Cartas de Vida e Patrimônio"

MAIN = """<main>
<article class="art" id="topo">
<header class="art-hero">
  <div class="wrap" style="max-width:880px">
    <div class="masthead">
      <span>Cartas de Vida e Patrimônio</span>
      <span class="sep"></span>
      <span>Inscrição confirmada</span>
    </div>
    <h1 class="h1">Inscrição confirmada.</h1>
    <p class="lead">A próxima carta chega ao seu e-mail. Para ela não cair no spam, vale adicionar leonardo@cartas.leonardodesousa.com.br aos seus contatos.</p>
  </div>
</header>
<div class="art-body">
  <p>Enquanto isso, as cartas já publicadas estão aqui: <a href="/cartas">Cartas de Vida e Patrimônio</a></p>
</div>
</article>
</main>"""


def main():
    h = gc.casca()
    h = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", h, flags=re.S)
    h = re.sub(r'<link rel="canonical"[^>]*>\n?', "", h)
    h = re.sub(r'<meta (property="og:|name="twitter:)[^>]*>\n?', "", h)
    h = re.sub(r'<meta name="description"[^>]*>\n?', "", h)
    h, n = re.subn(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, nofollow">', h, count=1)
    if n != 1:
        raise SystemExit("sobre.html mudou: não achei a meta robots")
    h, n = re.subn(r"<title>.*?</title>", f"<title>{TITULO}</title>", h, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("sobre.html mudou: não achei o title")
    h = h.replace("</style>", gc.CSS_CARTA + "</style>", 1)
    h, n = re.subn(r"<main>.*?</main>", lambda _m: MAIN, h, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("sobre.html mudou: não achei o <main>")
    destino = os.path.join(gc.RAIZ, "cartas", "confirmado.html")
    open(destino, "w", encoding="utf-8").write(h)
    print("gerado:", destino)


if __name__ == "__main__":
    main()
