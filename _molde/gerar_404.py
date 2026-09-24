"""Gera 404.html com a casca do site (cabeçalho, rodapé, fontes, cores de sobre.html).

Uso: python3 _molde/gerar_404.py
Rodar de novo sempre que o menu ou o rodapé de sobre.html mudarem.
A página é servida pelo ErrorDocument 404 do .htaccess e leva noindex.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_carta as gc  # noqa: E402

TITULO = "Página não encontrada · Leonardo Sousa"

MAIN = """<main>
<article class="art" id="topo">
<header class="art-hero">
  <div class="wrap" style="max-width:880px">
    <div class="masthead">
      <span>Erro 404</span>
      <span class="sep"></span>
      <span>Página não encontrada</span>
    </div>
    <h1 class="h1">Esta página não está aqui.</h1>
    <p class="lead">O link pode ter um erro de digitação ou apontar para um endereço antigo: o site foi refeito e algumas páginas mudaram de lugar.</p>
  </div>
</header>
<div class="art-body">
  <p>Por onde seguir:</p>
  <ul class="nf-lista">
    <li><a href="/">Início</a>: o que é o trabalho e para quem ele faz sentido.</li>
    <li><a href="/metodo">O método</a>: como o plano é montado, etapa por etapa.</li>
    <li><a href="/plano-exemplo">Plano de exemplo</a>: um Mapa Patrimonial completo, com dados fictícios.</li>
    <li><a href="/cartas">Cartas de Vida e Patrimônio</a>: textos sobre estrutura, proteção, impostos e sucessão. Quem chegou por um link antigo de carta encontra o texto por aqui.</li>
    <li><a href="/sobre">Sobre</a>: formação, certificações e forma de remuneração.</li>
  </ul>
  <p class="art-aviso">{aviso}</p>
</div>
</article>
{cta}
</main>"""

CSS_404 = """
.nf-lista{ list-style:none; padding:0; margin:18px 0 0; display:grid; gap:12px; }
.nf-lista li{ padding:14px 0; border-top:1px solid var(--line); }
.nf-lista a{ font-weight:600; color:var(--ink); }
"""


def main():
    h = gc.casca()
    # página de erro: sem dados estruturados, sem canonical, sem cartão social
    h = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", h, flags=re.S)
    h = re.sub(r'<link rel="canonical"[^>]*>\n?', "", h)
    h = re.sub(r'<meta (property="og:|name="twitter:)[^>]*>\n?', "", h)
    h = re.sub(r'<meta name="description"[^>]*>\n?', "", h)
    h, n = re.subn(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, follow">', h, count=1)
    if n != 1:
        raise SystemExit("sobre.html mudou: não achei a meta robots")
    h, n = re.subn(r"<title>.*?</title>", f"<title>{TITULO}</title>", h, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("sobre.html mudou: não achei o title")
    h = h.replace("</style>", gc.CSS_CARTA + CSS_404 + "</style>", 1)
    h, n = re.subn(r"<main>.*?</main>", lambda _m: MAIN.replace("{cta}", gc.secao_cta()).replace("{aviso}", gc.DISCLAIMER), h, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("sobre.html mudou: não achei o <main>")
    destino = os.path.join(gc.RAIZ, "404.html")
    open(destino, "w", encoding="utf-8").write(h)
    print("gerado:", destino)


if __name__ == "__main__":
    main()
