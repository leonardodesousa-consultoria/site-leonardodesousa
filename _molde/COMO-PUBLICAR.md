# Como publicar uma carta no site

Molde da Fase 4 do plano de AEO (22/09/2026). As cartas moram em `/cartas/<slug>` e são a principal forma de o site ser citado por ChatGPT, Perplexity, Gemini e Claude. Esta pasta `_molde/` não vai para o ar (está no `exclude` do deploy).

## Ordem de publicação da carta semanal

1. **Site primeiro.** Texto completo em `/cartas/<slug>`. É o original, e é o que as IAs citam.
2. **Substack no mesmo dia.** Mesmo texto, porque o e-mail é o canal da newsletter. O Substack não aceita apontar outro endereço como original, então publicar antes no site é o que garante a autoria. Depois de publicar, preencher o campo `substack:` da carta e gerar de novo.
3. **LinkedIn.** Versão adaptada, com link para a carta no site, não para o Substack.

A cadeia de sempre vale antes do passo 1: especialista quando houver número, lei ou tributo, depois crítico cego, `vendas-editor-chefe`, humanizer, anti-escrita e `vendas-compliance-cvm`.

## Passo a passo técnico

```bash
cd marca-consultoria/site-2026/site-kinghost-repo
cp _molde/modelo-carta.md _molde/cartas/<slug>.md
# escrever a carta
python3 _molde/gerar_carta.py _molde/cartas/<slug>.md
git add -A && git commit -m "site: carta <slug>" && git push
curl -s -o /dev/null -w "%{http_code}\n" https://leonardodesousa.com.br/cartas/<slug>
```

O gerador cria `cartas/<slug>.html` e atualiza `sitemap.xml`, `llms.txt` e a lista "Cartas recentes" de `/cartas`. Para corrigir uma carta já publicada, edite o `.md`, troque o campo `atualizado` e rode de novo. `--todas` regenera tudo, por exemplo depois de uma mudança no menu do site.

## Campos do cabeçalho

| Campo | Para que serve |
|---|---|
| `titulo` | Título da página. Escreva como a pergunta que a pessoa faria à IA. |
| `slug` | Endereço. Minúsculas, números e hífen. Não mude depois de publicar. |
| `descricao` | Meta description e linha do `llms.txt`. Até uns 160 caracteres. |
| `tema` | Rótulo curto: Sucessão, Proteção, Impostos, Estrutura, Método, Exterior. |
| `publicado` / `atualizado` | Datas no formato AAAA-MM-DD. |
| `resumo` | Linha de apoio abaixo do título. |
| `substack` | Opcional. Link da mesma carta no Substack. |
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
