"""Envio da carta semanal por e-mail (Broadcast do Resend, via backend).

Uso, sempre nesta ordem:
    python3 _molde/enviar_carta.py <slug> --previa             # abre o e-mail no navegador; não envia nada
    python3 _molde/enviar_carta.py <slug> --hash               # hash que o compliance aprova (compliance_audit)
    python3 _molde/enviar_carta.py <slug> --teste              # broadcast para o segmento Cartas-teste (só Leonardo)
    python3 _molde/enviar_carta.py <slug> --agendar 2026-10-01T09:00:00-03:00   # envio real, agendado

Antes: `python3 _molde/gerar_carta.py _molde/cartas/<slug>.md` (gera o site e _molde/saida/<slug>.email.*),
publicar a carta no site e passar a versão e-mail pela cadeia até o vendas-compliance-cvm, que grava
o hash de --hash em compliance_audit.

O backend recusa o envio real se: o hash (assunto + html + texto) não estiver aprovado; não houver
--teste enviado desta mesma versão; não for quinta-feira com 10 min de antecedência; faltar o link
de descadastro; as listas (Supabase x Resend) divergirem; a carta já tiver envio real agendado.

NUNCA validar este script rodando --agendar "para ver se funciona" (lição de 11/09/2026: testa-se o
gate, não o programa). Para ver o resultado, use --previa e --teste.

O token das rotas administrativas fica no Chaveiro do macOS (serviço cartas-admin-token).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = "https://luana-backend-production.up.railway.app"
DOMINIO = "https://leonardodesousa.com.br"
UNSUB = "{{{RESEND_UNSUBSCRIBE_URL}}}"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_carta as gc  # noqa: E402


def hash_peca(assunto: str, html: str, texto: str) -> str:
    """Mesma fórmula do backend (cartas.hash_peca)."""
    return hashlib.sha256("\n␞\n".join((assunto, html, texto)).encode()).hexdigest()


def carregar(slug: str):
    md = os.path.join(RAIZ, "_molde", "cartas", slug + ".md")
    if not os.path.exists(md):
        sys.exit(f"ERRO: não achei {md}")
    meta, _, _ = gc.ler_carta(md)
    saida = os.path.join(RAIZ, "_molde", "saida")
    ph, pt = os.path.join(saida, slug + ".email.html"), os.path.join(saida, slug + ".email.txt")
    if not (os.path.exists(ph) and os.path.exists(pt)):
        sys.exit("ERRO: rode antes o gerar_carta.py para esta carta")
    html, texto = open(ph, encoding="utf-8").read(), open(pt, encoding="utf-8").read()
    return meta, meta["titulo"], html, texto, ph


def checar_local(slug: str, assunto: str, html: str, texto: str) -> list[str]:
    erros = []
    for nome, t in (("assunto", assunto), ("html", html), ("texto", texto)):
        if "—" in t:
            erros.append(f"travessão no {nome}")
        if "!" in re.sub(r"<!DOCTYPE[^>]*>|<!--.*?-->|<!\[.*?\]>", "", t, flags=re.S):
            erros.append(f"exclamação no {nome}")
    if UNSUB not in html or UNSUB not in texto:
        erros.append("falta o link de descadastro")
    try:
        with urllib.request.urlopen(f"{DOMINIO}/cartas/{slug}", timeout=20) as r:
            if r.status != 200:
                erros.append(f"a carta não está no ar ({r.status})")
    except urllib.error.HTTPError as e:
        erros.append(f"a carta não está no ar ({e.code})")
    return erros


def token() -> str:
    try:
        return subprocess.run(["security", "find-generic-password", "-s", "cartas-admin-token",
                               "-a", "leonardo", "-w"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit("ERRO: token cartas-admin-token não está no Chaveiro")


def chamar(corpo: dict) -> tuple[int, dict]:
    req = urllib.request.Request(BACKEND + "/cartas/admin/broadcast", method="POST",
                                 data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {token()}"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    slug, modo = sys.argv[1], sys.argv[2]
    meta, assunto, html, texto, ph = carregar(slug)
    h = hash_peca(assunto, html, texto)

    if modo == "--previa":
        webbrowser.open("file://" + ph)
        print(f"prévia aberta: {ph}\nassunto: {assunto}\nnada foi enviado")
        return
    if modo == "--hash":
        print(h)
        return

    erros = checar_local(slug, assunto, html, texto)
    if erros:
        sys.exit("RECUSADO:\n- " + "\n- ".join(erros))

    corpo = {"slug": slug, "assunto": assunto, "html": html, "texto": texto, "email_hash": h}
    if modo == "--teste":
        corpo["modo"] = "teste"
    elif modo == "--agendar":
        if len(sys.argv) < 4:
            sys.exit("informe o horário, ex.: 2026-10-01T09:00:00-03:00")
        quando = datetime.fromisoformat(sys.argv[3])
        if quando.tzinfo is None:
            sys.exit("horário sem fuso: use -03:00 no fim")
        corpo.update(modo="real", agendar_para=quando.isoformat())
    else:
        sys.exit(__doc__)

    status, resp = chamar(corpo)
    if status == 409:
        sys.exit("RECUSADO pelo backend:\n- " + "\n- ".join(resp.get("recusado", [])))
    if status != 200:
        sys.exit(f"ERRO {status}: {resp}")
    print(json.dumps(resp, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
