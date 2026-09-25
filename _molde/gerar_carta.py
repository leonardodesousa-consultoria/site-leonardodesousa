#!/usr/bin/env python3
"""Gera uma carta do site em /cartas/<slug> a partir de um Markdown com front matter.

Uso (na raiz do repo do site):
    python3 _molde/gerar_carta.py _molde/cartas/<slug>.md
    python3 _molde/gerar_carta.py --todas          # regenera todas as cartas de _molde/cartas/

O que faz, de uma vez:
  1. cartas/<slug>.html com o cabeçalho, o rodapé e o consentimento do site
     (a casca vem de sobre.html, então qualquer mudança de menu vale para as cartas)
  2. schema BlogPosting + FAQPage + BreadcrumbList, autor e organização pelo @id
  3. sitemap.xml, llms.txt e a lista "Cartas recentes" de cartas.html atualizados

Sem dependência externa. O Markdown aceito está descrito em _molde/COMO-PUBLICAR.md.
"""
import datetime as dt
import glob
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carta_email  # noqa: E402  (versão e-mail da carta)
import inscricao  # noqa: E402  (formulário de inscrição nas cartas)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMINIO = "https://leonardodesousa.com.br"
ORG_ID = DOMINIO + "/#organizacao"
PERSON_ID = DOMINIO + "/sobre#leonardo-sousa"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
DISCLAIMER = ("As informações compartilhadas têm caráter educativo e não constituem recomendação "
              "de investimento. Para orientação personalizada, contate um consultor de investimentos.")
OBRIGATORIOS = ["titulo", "slug", "descricao", "tema", "publicado", "atualizado", "resumo"]


class ErroCarta(Exception):
    pass


# ---------------------------------------------------------------- leitura

def ler_carta(caminho):
    txt = open(caminho, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
    if not m:
        raise ErroCarta(f"{caminho}: falta o front matter entre linhas '---'")
    meta = {}
    for linha in m.group(1).splitlines():
        if not linha.strip() or linha.strip().startswith("#"):
            continue
        k, _, v = linha.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    faltam = [k for k in OBRIGATORIOS if not meta.get(k)]
    if faltam:
        raise ErroCarta(f"{caminho}: campos obrigatórios vazios: {', '.join(faltam)}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", meta["slug"]):
        raise ErroCarta(f"{caminho}: slug só com minúsculas, números e hífen")
    for k in ("publicado", "atualizado"):
        dt.date.fromisoformat(meta[k])
    corpo, faq = separar_faq(m.group(2))
    if "—" in txt:
        raise ErroCarta(f"{caminho}: tem travessão (—). Regra da marca: zero travessão")
    return meta, corpo, faq


def separar_faq(md):
    partes = re.split(r"^## Perguntas frequentes\s*$", md, flags=re.M)
    if len(partes) == 1:
        return md, []
    corpo, bloco = partes[0], partes[1]
    faq = []
    for m in re.finditer(r"^### (.+?)\n(.*?)(?=^### |\Z)", bloco, re.S | re.M):
        resposta = m.group(2).strip()
        if resposta:
            faq.append((m.group(1).strip(), resposta))
    return corpo, faq


# ---------------------------------------------------------------- markdown

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)

    def link(m):
        rot, url = m.group(1), m.group(2)
        ext = url.startswith("http") and "leonardodesousa.com.br" not in url
        extra = ' target="_blank" rel="noopener"' if ext else ""
        return f'<a href="{html.escape(url)}"{extra}>{rot}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)


def md_para_html(md):
    linhas = md.strip("\n").split("\n")
    out, i = [], 0
    while i < len(linhas):
        l = linhas[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith("## "):
            titulo = l[3:].strip()
            ancora = re.sub(r"[^a-z0-9]+", "-", normalizar(titulo)).strip("-")
            out.append(f'<h2 id="{ancora}">{inline(titulo)}</h2>')
            i += 1
        elif l.startswith("### "):
            out.append(f"<h3>{inline(l[4:].strip())}</h3>")
            i += 1
        elif l.startswith("> "):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("> "):
                bloco.append(linhas[i][2:])
                i += 1
            out.append(f'<p class="art-resposta">{inline(" ".join(bloco))}</p>')
        elif l.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("|"):
                bloco.append(linhas[i])
                i += 1
            out.append(tabela(bloco))
        elif re.match(r"^- ", l):
            itens = []
            while i < len(linhas) and linhas[i].startswith("- "):
                itens.append(f"<li>{inline(linhas[i][2:].strip())}</li>")
                i += 1
            out.append("<ul>" + "".join(itens) + "</ul>")
        elif re.match(r"^\d+\. ", l):
            itens = []
            while i < len(linhas) and re.match(r"^\d+\. ", linhas[i]):
                itens.append(f"<li>{inline(re.sub(r'^\d+\. ', '', linhas[i]).strip())}</li>")
                i += 1
            out.append("<ol>" + "".join(itens) + "</ol>")
        else:
            bloco = []
            while i < len(linhas) and linhas[i].strip() and not re.match(r"^(#{2,3} |> |\||- |\d+\. )", linhas[i]):
                bloco.append(linhas[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(bloco))}</p>")
    return "\n".join(out)


def tabela(linhas):
    cel = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    cab, corpo = cel(linhas[0]), [cel(l) for l in linhas[2:]]
    th = "".join(f'<th scope="col">{inline(c)}</th>' for c in cab)
    trs = "".join("<tr>" + "".join(
        (f'<th scope="row">{inline(c)}</th>' if j == 0 else f"<td>{inline(c)}</td>")
        for j, c in enumerate(r)) + "</tr>" for r in corpo)
    return f'<div class="art-tabela"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def texto_puro(md):
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", md)
    return re.sub(r"[*#>|]", "", t)


def normalizar(t):
    import unicodedata
    return unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()


def data_extenso(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


# ---------------------------------------------------------------- página

CSS_CARTA = """
.art-capa{ max-width:880px; margin:0 auto 2.2em; padding:0 var(--pad-x); }
.art-capa img{ display:block; width:100%; height:auto; border-radius:6px; }
/* ===== Carta do site (gerada por _molde/gerar_carta.py) ===== */
.art-hero{ padding-top:clamp(6.6rem,13vh,8.6rem); padding-bottom:clamp(1.6rem,3vw,2.4rem); }
.art-hero .h1{ font-size:clamp(2rem,5vw,3.3rem); max-width:22ch; margin-top:clamp(1.4rem,3vw,2rem); }
.art-hero .lead{ margin-top:18px; max-width:56ch; }
.art-by{ margin-top:22px; font-size:.9rem; color:var(--mut); display:flex; flex-wrap:wrap; gap:6px 14px; }
.art-by a{ color:var(--ink2); }
.art-body{ max-width:720px; margin:0 auto; padding-inline:var(--pad-x); padding-bottom:var(--sec-y); }
.art-body > *{ margin-top:1.1em; }
.art-body p, .art-body li{ font-size:1.08rem; line-height:1.72; color:var(--ink2); }
.art-body h2{ font-family:var(--serif); font-weight:600; font-size:clamp(1.4rem,2.6vw,1.8rem); line-height:1.2;
  color:var(--ink); margin-top:2.1em; letter-spacing:-.01em; scroll-margin-top:90px; }
.art-body h3{ font-family:var(--serif); font-weight:600; font-size:1.2rem; color:var(--ink); margin-top:1.6em; }
.art-body ul, .art-body ol{ padding-left:1.3em; }
.art-body li + li{ margin-top:.45em; }
.art-body a{ color:var(--accent-tx); text-underline-offset:3px; }
.art-body strong{ color:var(--ink); }
.art-resposta{ background:var(--paper); border-left:3px solid var(--accent); padding:18px 22px;
  font-family:var(--serif); font-size:1.14rem !important; line-height:1.6 !important; color:var(--ink) !important; }
.art-tabela{ overflow-x:auto; -webkit-overflow-scrolling:touch; }
.art-tabela table{ width:100%; min-width:520px; border-collapse:collapse; font-size:.96rem; background:var(--paper); }
.art-tabela th, .art-tabela td{ text-align:left; vertical-align:top; padding:12px 14px; border-bottom:1px solid var(--line); line-height:1.5; }
.art-tabela thead th{ font-weight:600; color:var(--ink); border-bottom:2px solid var(--ink); }
.art-tabela tbody th{ font-weight:600; color:var(--ink); }
.art-tabela td{ color:var(--ink2); }
.art-faq{ margin-top:2.4em !important; }
.art-faq h2{ margin-bottom:.2em; }
.faq{ margin-top:14px; border-top:1px solid var(--line); }
.faq details{ border-bottom:1px solid var(--line); }
.faq summary{ list-style:none; cursor:pointer; padding:20px 44px 20px 4px; position:relative;
  font-family:var(--serif); font-size:clamp(1.06rem,1.9vw,1.24rem); font-weight:500; color:var(--ink); transition:color .2s; }
.faq summary::-webkit-details-marker{ display:none; }
.faq summary:hover{ color:var(--accent-tx); }
.faq summary::after{ content:'+'; position:absolute; right:6px; top:50%; transform:translateY(-50%);
  font-family:var(--sans); font-size:1.5rem; font-weight:300; color:var(--accent-tx); transition:transform .25s; }
.faq details[open] summary::after{ transform:translateY(-50%) rotate(45deg); }
.faq .fb{ padding:0 44px 22px 4px; }
.faq .fb p{ color:var(--ink2); line-height:1.62; }
.art-autor{ display:flex; gap:18px; align-items:center; margin-top:2.6em !important; padding:22px;
  background:var(--paper); border:1px solid var(--line-soft); }
.art-autor img{ width:64px; height:64px; border-radius:50%; object-fit:cover; flex:none; }
.art-autor p{ font-size:.96rem !important; line-height:1.55 !important; margin:0; }
.art-autor .nm{ font-family:var(--serif); font-weight:600; color:var(--ink); font-size:1.06rem !important; }
.art-aviso{ font-size:.86rem !important; color:var(--mut) !important; line-height:1.55 !important; }
@media (max-width:560px){ .art-autor{ flex-direction:column; align-items:flex-start; } }
"""


def casca():
    """Cabeçalho, rodapé e scripts do site, tirados de sobre.html."""
    h = open(os.path.join(RAIZ, "sobre.html"), encoding="utf-8").read()
    for marca in ("<main>", "</main>", "</head>", "</style>"):
        if marca not in h:
            raise ErroCarta(f"sobre.html mudou de estrutura: não achei {marca}")
    # blocos JSON-LD próprios do /sobre (perfil e FAQ) saem; os da organização ficam
    def filtra(m):
        return "" if ('"ProfilePage"' in m.group(0) or '"FAQPage"' in m.group(0)) else m.group(0)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', filtra, h, flags=re.S)
    h = h.replace(' aria-current="page"', "")
    # links relativos passam a absolutos, porque a carta mora em /cartas/
    h = re.sub(r'(href|src)="(?!https?:|/|#|mailto:|tel:|data:)([^"]+?)\.html"', r'\1="/\2"', h)
    h = re.sub(r'(href|src)="(?!https?:|/|#|mailto:|tel:|data:)([^"]+)"', r'\1="/\2"', h)
    h = h.replace('href="/index"', 'href="/"')
    return h


def trocar_meta(h, meta, url):
    titulo = f'{meta["titulo"]} · Leonardo Sousa'
    desc = html.escape(meta["descricao"], quote=True)
    t = html.escape(titulo, quote=True)
    subs = [
        (r"<title>.*?</title>", f"<title>{html.escape(titulo)}</title>"),
        (r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">'),
        (r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">'),
        (r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{t}">'),
        (r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">'),
        (r'<meta property="og:type" content="[^"]*">', '<meta property="og:type" content="article">'),
        (r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">'),
        (r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{t}">'),
        (r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{desc}">'),
    ]
    for padrao, novo in subs:
        h, n = re.subn(padrao, lambda _m, novo=novo: novo, h, count=1, flags=re.S)
        if n != 1:
            raise ErroCarta(f"sobre.html mudou: não achei a tag {padrao}")
    return h


def schema(meta, url, faq):
    grafo = [{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "@id": url + "#carta",
        "mainEntityOfPage": url,
        "url": url,
        "headline": meta["titulo"],
        "description": meta["descricao"],
        "inLanguage": "pt-BR",
        "datePublished": meta["publicado"] + "T09:00:00-03:00",
        "dateModified": meta["atualizado"] + "T09:00:00-03:00",
        "articleSection": meta["tema"],
        "image": DOMINIO + "/opengraph.jpg",
        "author": {"@type": "Person", "@id": PERSON_ID, "name": "Leonardo Sousa",
                   "jobTitle": "Consultor Patrimonial", "url": DOMINIO + "/sobre"},
        "publisher": {"@type": "Organization", "@id": ORG_ID,
                      "name": "Leonardo Sousa - Consultoria Patrimonial Independente",
                      "logo": {"@type": "ImageObject", "url": DOMINIO + "/favicon.png"}},
        "isPartOf": {"@type": "Blog", "name": "Cartas de Vida e Patrimônio", "url": DOMINIO + "/cartas"},
    }, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": DOMINIO + "/"},
            {"@type": "ListItem", "position": 2, "name": "Cartas", "item": DOMINIO + "/cartas"},
            {"@type": "ListItem", "position": 3, "name": meta["titulo"], "item": url},
        ],
    }]
    if faq:
        grafo.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": texto_puro(r).strip()}}
                           for q, r in faq],
        })
    return "".join('<script type="application/ld+json">\n' + json.dumps(g, ensure_ascii=False, indent=2)
                   + "\n</script>\n" for g in grafo)


CAPA_NA_PAGINA = True   # False: capa só no compartilhamento, no schema e no e-mail


def preparar_capa(slug):
    """Gera webp e jpg a partir de _molde/capas/<slug>.png. Devolve as URLs ou None."""
    origem = os.path.join(RAIZ, "_molde", "capas", slug + ".png")
    pasta = os.path.join(RAIZ, "cartas", "img")
    webp, jpg = os.path.join(pasta, slug + ".webp"), os.path.join(pasta, slug + ".jpg")
    if os.path.exists(origem):
        from PIL import Image
        os.makedirs(pasta, exist_ok=True)
        if not os.path.exists(jpg) or os.path.getmtime(jpg) < os.path.getmtime(origem):
            im = Image.open(origem).convert("RGB")
            im.resize((1600, 840), Image.LANCZOS).save(webp, "WEBP", quality=78, method=6)
            im.resize((1200, 630), Image.LANCZOS).save(jpg, "JPEG", quality=82, optimize=True, progressive=True)
    if os.path.exists(jpg) and os.path.exists(webp):
        return {"webp": f"/cartas/img/{slug}.webp", "jpg": f"{DOMINIO}/cartas/img/{slug}.jpg"}
    return None


def montar(meta, corpo, faq):
    url = f'{DOMINIO}/cartas/{meta["slug"]}'
    palavras = len(texto_puro(corpo + " ".join(q + " " + r for q, r in faq)).split())
    minutos = max(1, round(palavras / 200))
    h = casca()
    h = trocar_meta(h, meta, url)
    capa = preparar_capa(meta["slug"])
    if capa:
        h = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*(")',
                   lambda m: m.group(1) + capa["jpg"] + m.group(2), h)
    h = h.replace("</style>", CSS_CARTA + inscricao.CSS + "</style>", 1)
    h = h.replace("</body>", inscricao.js() + "\n</body>", 1)
    esquema = schema(meta, url, faq)
    if capa:
        esquema = esquema.replace(f'"{DOMINIO}/opengraph.jpg"', f'"{capa["jpg"]}"')
    h = h.replace("</head>", esquema + "</head>", 1)

    faq_html = ""
    if faq:
        itens = "".join(f"<details><summary>{inline(q)}</summary><div class=\"fb\">{md_para_html(r)}</div></details>"
                        for q, r in faq)
        faq_html = f'<section class="art-faq" aria-labelledby="faq"><h2 id="faq">Perguntas frequentes</h2><div class="faq">{itens}</div></section>'
    receber = inscricao.bloco(origem=f'carta:{meta["slug"]}', kicker="Cartas de Vida e Patrimônio",
                              titulo="Receba a próxima carta",
                              apoio="Uma carta por semana, no seu e-mail.")
    atualizado = ""
    if meta["atualizado"] != meta["publicado"]:
        atualizado = f'<span>Atualizada em <time datetime="{meta["atualizado"]}">{data_extenso(meta["atualizado"])}</time></span>'

    figura_capa = ""
    if capa and CAPA_NA_PAGINA:
        figura_capa = (f'<figure class="art-capa"><img src="{capa["webp"]}" width="1600" height="840" '
                       f'alt="Capa da carta: {html.escape(meta["titulo"], quote=True)}" decoding="async"></figure>')
    main = f"""<main>
<article class="art" id="topo">
<header class="art-hero">
  <div class="wrap" style="max-width:880px">
    <div class="masthead">
      <span><a href="/cartas" style="color:inherit;text-decoration:none">Cartas de Vida e Patrimônio</a></span>
      <span class="sep"></span>
      <span>{html.escape(meta["tema"])}</span>
    </div>
    <h1 class="h1">{inline(meta["titulo"])}</h1>
    <p class="lead">{inline(meta["resumo"])}</p>
    <p class="art-by">
      <span>Por <a href="/sobre">Leonardo Sousa</a>, Consultor Patrimonial</span>
      <span>Publicada em <time datetime="{meta["publicado"]}">{data_extenso(meta["publicado"])}</time></span>
      {atualizado}
      <span>{minutos} min de leitura</span>
    </p>
  </div>
</header>
{figura_capa}
<div class="art-body">
{md_para_html(corpo)}
{faq_html}
<aside class="art-autor" aria-label="Sobre o autor">
  <img src="/foto-leo.webp" alt="Leonardo Sousa" width="64" height="64" loading="lazy">
  <div>
    <p class="nm">Leonardo Sousa</p>
    <p>Consultor patrimonial independente, remunerado por fee fixo anual e sem comissão de produto. Certificação CEA ANBIMA. <a href="/sobre">Conheça a formação e o método</a>.</p>
  </div>
</aside>
<div style="margin-top:2.4em">
{receber}
</div>
<p class="art-aviso">{DISCLAIMER}</p>
</div>
</article>
{secao_cta()}
</main>"""
    h = re.sub(r"<main>.*?</main>", lambda _m: main, h, count=1, flags=re.S)
    return h


def secao_cta():
    h = open(os.path.join(RAIZ, "sobre.html"), encoding="utf-8").read()
    m = re.search(r'<section class="sec final" id="conversa">.*?</section>', h, re.S)
    if not m:
        raise ErroCarta("sobre.html mudou: não achei a seção final de conversa")
    return m.group(0)


# ---------------------------------------------------------------- índices

def todas_as_cartas():
    cartas = []
    for f in sorted(glob.glob(os.path.join(RAIZ, "_molde", "cartas", "*.md"))):
        meta, _, _ = ler_carta(f)
        if meta.get("rascunho", "").lower() in ("sim", "true", "1"):
            continue
        cartas.append(meta)
    return sorted(cartas, key=lambda m: m["publicado"], reverse=True)


def atualizar_sitemap(cartas):
    p = os.path.join(RAIZ, "sitemap.xml")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"\s*<url><loc>https://leonardodesousa\.com\.br/cartas/[^<]+</loc>.*?</url>", "", s, flags=re.S)
    novas = "".join(f'\n  <url><loc>{DOMINIO}/cartas/{c["slug"]}</loc><lastmod>{c["atualizado"]}</lastmod>'
                    f'<changefreq>yearly</changefreq><priority>0.7</priority></url>' for c in cartas)
    s = s.replace("\n</urlset>", novas + "\n</urlset>")
    open(p, "w", encoding="utf-8").write(s)


def atualizar_llms(cartas):
    p = os.path.join(RAIZ, "llms.txt")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"\n## Cartas no site\n.*?(?=\n## |\Z)", "", s, flags=re.S)
    if cartas:
        linhas = "\n".join(f'- [{c["titulo"]}]({DOMINIO}/cartas/{c["slug"]}): {c["descricao"]}' for c in cartas)
        bloco = f"\n## Cartas no site\n\n{linhas}\n"
        s = s.replace("\n## Onde mais publica", bloco + "\n## Onde mais publica", 1)
    open(p, "w", encoding="utf-8").write(s)


def atualizar_indice(cartas):
    p = os.path.join(RAIZ, "cartas.html")
    s = open(p, encoding="utf-8").read()
    ini, fim = "<!-- CARTAS-SITE:INICIO -->", "<!-- CARTAS-SITE:FIM -->"
    if ini not in s:
        s = s.replace('<div class="toc rev d2">', f'<div class="toc rev d2">\n      {ini}\n      {fim}', 1)
    itens = "".join(f"""
      <a class="toc-item" href="/cartas/{c["slug"]}">
        <span class="toc-no num">00</span>
        <span class="toc-main">
          <span class="toc-meta">{html.escape(c["tema"])} <span class="date num">{data_extenso(c["publicado"])}</span></span>
          <h3>{html.escape(c["titulo"])}</h3>
          <span class="toc-sub">{html.escape(c["descricao"])}</span>
        </span>
        <span class="toc-go">Ler a carta</span>
      </a>""" for c in cartas)
    s = re.sub(re.escape(ini) + r".*?" + re.escape(fim), lambda _m: ini + itens + "\n      " + fim, s, count=1, flags=re.S)
    contador = iter(range(1, 999))
    s = re.sub(r'<span class="toc-no num">\d+</span>', lambda _m: f'<span class="toc-no num">{next(contador):02d}</span>', s)
    open(p, "w", encoding="utf-8").write(s)


# ---------------------------------------------------------------- main

def gerar(caminho):
    meta, corpo, faq = ler_carta(caminho)
    os.makedirs(os.path.join(RAIZ, "cartas"), exist_ok=True)
    destino = os.path.join(RAIZ, "cartas", meta["slug"] + ".html")
    open(destino, "w", encoding="utf-8").write(montar(meta, corpo, faq))
    saida = os.path.join(RAIZ, "_molde", "saida")
    os.makedirs(saida, exist_ok=True)
    capa = preparar_capa(meta["slug"])
    doc, texto = carta_email.montar_email(meta, corpo, faq, md_para_html, DOMINIO, DISCLAIMER,
                                          capa_url=capa["jpg"] if capa else None)
    if "\u2014" in texto:
        raise ErroCarta("a versão e-mail tem travessão")
    open(os.path.join(saida, meta["slug"] + ".email.html"), "w", encoding="utf-8").write(doc)
    open(os.path.join(saida, meta["slug"] + ".email.txt"), "w", encoding="utf-8").write(texto)
    print(f"ok  /cartas/{meta['slug']}  ({len(faq)} perguntas no FAQ)")


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    arquivos = sorted(glob.glob(os.path.join(RAIZ, "_molde", "cartas", "*.md"))) if args == ["--todas"] else args
    try:
        for a in arquivos:
            meta, _, _ = ler_carta(a)
            if meta.get("rascunho", "").lower() in ("sim", "true", "1"):
                print(f"pula (rascunho)  {a}")
                continue
            gerar(a)
        cartas = todas_as_cartas()
        atualizar_sitemap(cartas)
        atualizar_llms(cartas)
        atualizar_indice(cartas)
        print(f"sitemap, llms.txt e /cartas atualizados ({len(cartas)} cartas no site)")
    except ErroCarta as e:
        sys.exit(f"ERRO: {e}")


if __name__ == "__main__":
    main()
