"""Componente de inscrição nas Cartas de Vida e Patrimônio (formulário + CSS + JS).

Uma fonte só para /cartas (cartas.html) e para o fim de cada carta (gerar_carta.py),
para os dois nunca divergirem. O envio vai para o backend (POST /cartas/inscrever),
que manda o e-mail de confirmação. Textos aprovados pela cadeia de peça pública em
25/09/2026 (compliance_audit d00c641c): mudou o texto, passa pela cadeia de novo.
"""
import html

BACKEND = "https://luana-backend-production.up.railway.app"

MICRO = ('Você recebe um e-mail para confirmar a inscrição. Uso seu endereço só para enviar '
         'as cartas. <a href="/privacidade">Política de Privacidade</a>')
MSG_OK = ("Falta um passo. Mandei um e-mail para você confirmar a inscrição. Se não aparecer "
          "em alguns minutos, olhe a pasta de spam ou de promoções.")
MSG_ERRO = "Não consegui registrar agora. Tente de novo em alguns minutos."

CSS = """
.insc{ background:linear-gradient(150deg,#15402c,#0a1914); color:#fff; border-radius:6px;
  padding:clamp(26px,4vw,40px); position:relative; }
.insc .insc-k{ font-size:.72rem; font-weight:600; letter-spacing:.18em; text-transform:uppercase; color:#3ecf8e; margin:0 0 10px; }
.insc h3{ font-family:var(--serif); font-size:clamp(1.3rem,2.4vw,1.7rem); font-weight:600; color:#fff; line-height:1.25; margin:0 0 10px; }
.insc .insc-ap{ color:rgba(255,255,255,.78); margin:0 0 20px; }
.insc form{ display:flex; flex-wrap:wrap; gap:10px; margin:0; }
.insc input[type=email]{ flex:1 1 220px; min-width:0; font:inherit; font-size:1rem; color:#fff;
  background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.28); border-radius:6px; padding:14px 16px; }
.insc input[type=email]::placeholder{ color:rgba(255,255,255,.62); }
.insc input[type=email]:focus{ outline:2px solid #3ecf8e; outline-offset:1px; }
.insc button{ font-family:var(--sans); font-weight:600; font-size:1rem; color:#062015; background:#3ecf8e;
  border:0; border-radius:6px; padding:14px 22px; cursor:pointer; }
.insc button:hover{ background:#4ad998; }
.insc button[disabled]{ opacity:.6; cursor:wait; }
.insc .insc-hp{ position:absolute; left:-9999px; width:1px; height:1px; overflow:hidden; }
.insc .insc-sr{ position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); border:0; }
.insc .insc-micro{ margin:14px 0 0; font-size:.84rem; line-height:1.5; color:rgba(255,255,255,.78); }
.insc .insc-micro a{ color:#3ecf8e; text-decoration:underline; text-underline-offset:2px; }
.insc .insc-ret{ margin:14px 0 0; font-size:.98rem; line-height:1.5; color:#fff; }
.insc .insc-ret:empty{ display:none; }
.insc .insc-ret.err{ color:#ffc9bb; }
"""

JS = """<script>
(function(){
  var URL_='%(backend)s/cartas/inscrever', OK=%(ok)s, ERRO=%(erro)s;
  Array.prototype.forEach.call(document.querySelectorAll('form.insc-f'), function(f){
    var ret=f.parentNode.querySelector('.insc-ret'), bt=f.querySelector('button'), em=f.querySelector('input[type=email]');
    f.addEventListener('submit', function(ev){
      ev.preventDefault();
      if(!f.reportValidity()) return;
      bt.disabled=true; ret.className='insc-ret'; ret.textContent='';
      fetch(URL_,{method:'POST',headers:{'Content-Type':'application/json'},keepalive:true,
        body:JSON.stringify({email:em.value.trim(), origem:f.getAttribute('data-origem')||'/cartas',
                             site:(f.querySelector('.insc-hp')||{}).value||''})})
      .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(){
        f.style.display='none'; ret.textContent=OK;
        try{ if(window.gtag) gtag('event','inscricao_cartas',{origem:f.getAttribute('data-origem')}); }catch(e){}
      })
      .catch(function(){ bt.disabled=false; ret.className='insc-ret err'; ret.textContent=ERRO; });
    });
  });
})();
</script>"""


def js() -> str:
    import json
    return JS % {"backend": BACKEND, "ok": json.dumps(MSG_OK, ensure_ascii=False),
                 "erro": json.dumps(MSG_ERRO, ensure_ascii=False)}


def bloco(origem: str, kicker: str, titulo: str, apoio: str = "", uid: str = "1") -> str:
    ap = f'<p class="insc-ap">{html.escape(apoio)}</p>' if apoio else ""
    o = html.escape(origem, quote=True)
    return f"""<div class="insc" id="receber">
  <p class="insc-k">{html.escape(kicker)}</p>
  <h3>{html.escape(titulo)}</h3>
  {ap}
  <form class="insc-f" data-origem="{o}" novalidate>
    <label class="insc-sr" for="insc-email-{uid}">Seu e-mail</label>
    <input id="insc-email-{uid}" type="email" name="email" autocomplete="email" inputmode="email" placeholder="Seu e-mail" required>
    <input class="insc-hp" type="text" name="site" tabindex="-1" autocomplete="off" aria-hidden="true">
    <button type="submit">Quero receber</button>
  </form>
  <p class="insc-micro">{MICRO}</p>
  <p class="insc-ret" role="status" aria-live="polite"></p>
</div>"""
