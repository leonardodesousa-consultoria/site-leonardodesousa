"""Versão e-mail de uma carta: HTML de e-mail (tabela, estilos inline) e texto puro.

Chamado por gerar_carta.py. Grava em _molde/saida/<slug>.email.html e .email.txt,
fora do deploy. O .email.txt é o texto que o compliance aprova (o hash dele vai para
compliance_audit) e é o que o backend confere antes do envio real.

Moldura aprovada pela cadeia de peça pública em 25/09/2026 (compliance_audit
d00c641c). Zero CTA: a seção de conversa da página do site não entra no e-mail
(regra da marca-substack-newsletter-engine). Zero itálico, Georgia e Arial.
"""
import html
import re

SERIF = "Georgia,'Times New Roman',serif"
SANS = "Arial,Helvetica,sans-serif"
INK, INK2, VERDE, LINHA, PAPEL = "#0a1914", "#2d4a3e", "#15804f", "#e3e5e0", "#f5f5f0"

RODAPE_MOTIVO = ("Você recebe esta carta porque se inscreveu nas Cartas de Vida e Patrimônio, "
                 "no site ou no Substack. Para não receber mais,")
AVISO_TRANSICAO = ("As Cartas de Vida e Patrimônio agora saem do meu site, e não mais pelo Substack. "
                   "Você continua inscrito e não precisa fazer nada. Para sair, basta um clique "
                   "no link do rodapé.")
UNSUB = "{{{RESEND_UNSUBSCRIBE_URL}}}"


def _absolutos(h: str, dominio: str) -> str:
    return re.sub(r'href="/', f'href="{dominio}/', h)


def _estilizar(h: str) -> str:
    """Troca as tags do md_para_html por versões com estilo inline de e-mail."""
    p = f"margin:0 0 18px 0;font-family:{SERIF};font-size:17px;line-height:27px;color:{INK};"
    subs = [
        (r'<p class="art-resposta">', f'<p style="{p}border-left:3px solid {VERDE};padding-left:16px;color:{INK2};">'),
        (r"<p>", f'<p style="{p}">'),
        (r'<h2 id="[^"]*">', f'<h2 style="margin:32px 0 12px 0;font-family:{SERIF};font-size:22px;line-height:29px;font-weight:bold;color:{INK};">'),
        (r"<h3>", f'<h3 style="margin:24px 0 8px 0;font-family:{SANS};font-size:17px;line-height:24px;font-weight:bold;color:{INK};">'),
        (r"<ul>", f'<ul style="margin:0 0 18px 0;padding-left:22px;font-family:{SERIF};font-size:17px;line-height:27px;color:{INK};">'),
        (r"<ol>", f'<ol style="margin:0 0 18px 0;padding-left:22px;font-family:{SERIF};font-size:17px;line-height:27px;color:{INK};">'),
        (r"<li>", '<li style="margin:0 0 8px 0;">'),
        (r"<em>", '<strong style="font-style:normal;font-weight:bold;">'),
        (r"</em>", "</strong>"),
        (r'<div class="art-tabela"><table>', f'<table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 20px 0;border-collapse:collapse;font-family:{SANS};font-size:15px;line-height:21px;color:{INK};">'),
        (r"</table></div>", "</table>"),
        (r'<th scope="col">', f'<th align="left" style="padding:8px 10px;border-bottom:2px solid {INK};font-weight:bold;">'),
        (r'<th scope="row">', f'<th align="left" style="padding:8px 10px;border-bottom:1px solid {LINHA};font-weight:bold;">'),
        (r"<td>", f'<td style="padding:8px 10px;border-bottom:1px solid {LINHA};">'),
        (r' target="_blank" rel="noopener"', ""),
        (r"<a href=", f'<a style="color:{VERDE};text-decoration:underline;" href='),
    ]
    for a, b in subs:
        h = re.sub(a, b, h)
    return h


def _texto(md: str, dominio: str) -> str:
    """Markdown da carta em texto puro legível."""
    t = re.sub(r"\[([^\]]+)\]\((/[^)\s]*)\)", lambda m: f"{m.group(1)} ({dominio}{m.group(2)})", md)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r"\1 (\2)", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", t)
    t = re.sub(r"^#{2,3} ", "", t, flags=re.M)
    t = re.sub(r"^> ", "", t, flags=re.M)
    linhas = []
    for l in t.split("\n"):
        if re.match(r"^\|\s*-", l):
            continue
        if l.startswith("|"):
            l = "  ".join(c.strip() for c in l.strip().strip("|").split("|"))
        linhas.append(l)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


def montar_email(meta: dict, corpo: str, faq: list, md_para_html, dominio: str,
                 disclaimer: str, capa_url: str | None = None) -> tuple[str, str]:
    url = f'{dominio}/cartas/{meta["slug"]}'
    aviso = str(meta.get("aviso_transicao", "")).lower() in ("sim", "true", "1")
    titulo, resumo = meta["titulo"], meta["resumo"]

    corpo_html = _estilizar(_absolutos(md_para_html(corpo), dominio))
    faq_html = ""
    if faq:
        faq_md = "## Perguntas frequentes\n\n" + "\n\n".join(f"### {q}\n{r}" for q, r in faq)
        faq_html = _estilizar(_absolutos(md_para_html(faq_md), dominio))
    caixa_aviso = ""
    if aviso:
        caixa_aviso = (f'<p style="margin:0 0 24px 0;padding:14px 16px;background:{PAPEL};font-family:{SANS};'
                       f'font-size:15px;line-height:22px;color:{INK2};">{html.escape(AVISO_TRANSICAO)}</p>')
    e = html.escape
    linha_capa = ""
    if capa_url:
        linha_capa = (f'<tr><td style="padding-top:14px;padding-left:32px;padding-right:32px;">'
                      f'<a href="{url}"><img src="{capa_url}" width="536" height="281" alt="{e(titulo)}" '
                      f'style="display:block;width:100%;max-width:536px;height:auto;border:0;border-radius:4px;"></a></td></tr>\n')
    pequeno = f"font-family:{SANS};font-size:13px;line-height:19px;color:{INK2};"
    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>{e(titulo)}</title>
</head>
<body style="margin:0;padding:0;background-color:{PAPEL};">
<span style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{e(resumo)}</span>
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{PAPEL}" style="background-color:{PAPEL};">
<tr><td align="center" style="padding-top:24px;padding-bottom:24px;padding-left:12px;padding-right:12px;">
<table width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="width:100%;max-width:600px;background-color:#ffffff;">
<tr><td style="padding-top:26px;padding-bottom:6px;padding-left:32px;padding-right:32px;">
<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
<td style="font-family:{SANS};font-size:12px;line-height:16px;letter-spacing:2px;text-transform:uppercase;color:{VERDE};font-weight:bold;">Cartas de Vida e Patrimônio</td>
<td align="right" style="font-family:{SANS};font-size:13px;line-height:16px;"><a href="{url}" style="color:{VERDE};text-decoration:underline;">Ler no site</a></td>
</tr></table>
</td></tr>
{linha_capa}<tr><td style="padding-top:18px;padding-bottom:8px;padding-left:32px;padding-right:32px;">
<h1 style="margin:0 0 12px 0;font-family:{SERIF};font-size:28px;line-height:34px;font-weight:bold;color:{INK};">{e(titulo)}</h1>
<p style="margin:0 0 24px 0;font-family:{SERIF};font-size:18px;line-height:27px;color:{INK2};">{e(resumo)}</p>
{caixa_aviso}
{corpo_html}
{faq_html}
</td></tr>
<tr><td style="padding-top:18px;padding-bottom:30px;padding-left:32px;padding-right:32px;border-top:1px solid {LINHA};">
<p style="margin:0 0 12px 0;font-family:{SERIF};font-size:16px;line-height:23px;color:{INK};"><strong>Leonardo Sousa</strong> · Consultor Patrimonial · <a href="{dominio}" style="color:{VERDE};text-decoration:underline;">leonardodesousa.com.br</a></p>
<p style="margin:0 0 12px 0;{pequeno}">{e(disclaimer)}</p>
<p style="margin:0;{pequeno}">{e(RODAPE_MOTIVO)} <a href="{UNSUB}" style="color:{VERDE};text-decoration:underline;">cancele a inscrição</a>.</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""

    partes = ["CARTAS DE VIDA E PATRIMÔNIO", "", titulo, "", resumo, "", f"Ler no site: {url}", ""]
    if aviso:
        partes += [AVISO_TRANSICAO, ""]
    partes.append(_texto(corpo, dominio))
    if faq:
        partes += ["", "Perguntas frequentes", ""]
        for q, r in faq:
            partes += [q, _texto(r, dominio), ""]
    partes += ["", "Leonardo Sousa · Consultor Patrimonial · leonardodesousa.com.br", "",
               disclaimer, "", f"{RODAPE_MOTIVO} cancele a inscrição: {UNSUB}"]
    texto = re.sub(r"\n{3,}", "\n\n", "\n".join(partes)).strip() + "\n"
    return doc, texto
