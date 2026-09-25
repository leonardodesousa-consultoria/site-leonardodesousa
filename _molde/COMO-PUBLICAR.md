# Como publicar uma carta no site

Molde da Fase 4 do plano de AEO (22/09/2026). As cartas moram em `/cartas/<slug>` e são a principal forma de o site ser citado por ChatGPT, Perplexity, Gemini e Claude. Esta pasta `_molde/` não vai para o ar (está no `exclude` do deploy).

## Ordem de publicação da carta semanal (desde 01/10/2026)

1. **Site primeiro.** Texto completo em `/cartas/<slug>`. É o original, e é o que as IAs citam.
2. **E-mail no mesmo dia, quinta às 9h**, pelo sistema próprio (Resend, subdomínio `cartas.leonardodesousa.com.br`). O Substack deixou de enviar: virou arquivo das cartas antigas.
3. **LinkedIn.** Versão adaptada, com link para a carta no site.

A cadeia de sempre vale antes do passo 1: especialista quando houver número, lei ou tributo, depois crítico cego, `vendas-editor-chefe`, humanizer, anti-escrita e `vendas-compliance-cvm`. A versão e-mail passa pelo mesmo compliance: o hash dela é o que libera o envio.

## Passo a passo técnico

```bash
cd marca-consultoria/site-2026/site-kinghost-repo
cp _molde/modelo-carta.md _molde/cartas/<slug>.md
# escrever a carta
python3 _molde/gerar_carta.py _molde/cartas/<slug>.md    # gera o site e _molde/saida/<slug>.email.html/.txt
git add -A && git commit -m "site: carta <slug>" && git push
curl -s -o /dev/null -w "%{http_code}\n" https://leonardodesousa.com.br/cartas/<slug>

python3 _molde/enviar_carta.py <slug> --previa             # olhar o e-mail; não envia nada
python3 _molde/enviar_carta.py <slug> --hash               # o compliance grava este hash em compliance_audit
python3 _molde/enviar_carta.py <slug> --teste              # chega só na caixa leonardo@leonardodesousa.com.br
python3 _molde/enviar_carta.py <slug> --agendar 2026-10-01T09:00:00-03:00
```

O gerador cria `cartas/<slug>.html`, a versão e-mail em `_molde/saida/` e atualiza `sitemap.xml`, `llms.txt` e a lista de `/cartas`. Para corrigir uma carta já publicada, edite o `.md`, troque o campo `atualizado` e rode de novo. `--todas` regenera tudo, por exemplo depois de uma mudança no menu do site.

**O envio real recusa sozinho** se: o hash (assunto, HTML e texto) não estiver aprovado; não houver `--teste` enviado desta versão; não for quinta com 10 minutos de antecedência; faltar o link de descadastro; as listas do Supabase e do Resend divergirem; a carta já tiver envio agendado. Nunca rodar `--agendar` "para testar": para ver o resultado existem `--previa` e `--teste`.

**Assinantes:** tabela `cartas_assinantes` no Supabase (fora de `leads_funil`: quem assina as cartas não entra na Luana nem na nutrição). Descadastro pelo link do rodapé de cada carta, sincronizado pelo webhook do Resend. Pedido de remoção por resposta de e-mail: `POST /cartas/admin/remover` (token no Chaveiro, serviço `cartas-admin-token`).

**Aviso de transição:** `aviso_transicao: sim` no cabeçalho da carta põe no topo do e-mail o aviso de que as cartas saíram do Substack. Usar só na primeira carta enviada pelo sistema novo.

## Campos do cabeçalho

| Campo | Para que serve |
|---|---|
| `titulo` | Título da página. Escreva como a pergunta que a pessoa faria à IA. |
| `slug` | Endereço. Minúsculas, números e hífen. Não mude depois de publicar. |
| `descricao` | Meta description e linha do `llms.txt`. Até uns 160 caracteres. |
| `tema` | Rótulo curto: Sucessão, Proteção, Impostos, Estrutura, Método, Exterior. |
| `publicado` / `atualizado` | Datas no formato AAAA-MM-DD. |
| `resumo` | Linha de apoio abaixo do título. |
| `substack` | Opcional. Link da versão antiga no Substack (não aparece mais na página). |
| `aviso_transicao` | Opcional. `sim` só na primeira carta enviada pelo sistema próprio. |
| `rascunho` | Opcional. `sim` faz o gerador pular a carta. |

## Como escrever para ser citada

- **Primeiro bloco = a resposta.** Comece com `> ` e responda à pergunta do título em 2 a 4 frases que se sustentem sozinhas. É o trecho que as IAs copiam.
- **Um `##` por subpergunta**, com blocos que façam sentido fora do contexto.
- **Tabela quando houver comparação** (`| a | b |`). As IAs extraem tabelas bem.
- **Lei, número e data com fonte**, na própria frase: "Lei 15.040/2024, art. 115".
- **`## Perguntas frequentes` no fim**, com `### pergunta` e a resposta embaixo. Vira FAQ visível e schema. Só perguntas que alguém faz de verdade: Luana, conversas exploratórias, a lista de prompts do placar.
- **Zero travessão.** O gerador recusa o arquivo se houver um.
- Nada de recomendação de produto específico, promessa de retorno ou nome de cliente.

## Markdown aceito

`## título`, `### subtítulo`, parágrafo, `- lista`, `1. lista numerada`, `> resposta direta`, tabela com `|`, `**negrito**`, `*itálico*`, `[texto](url)`. Link interno começa com `/` (ex.: `/metodo`).
