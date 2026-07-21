# site-leonardodesousa

Site institucional (`leonardodesousa.com.br`). HTML estático, sem build, sem backend.
Fonte canônica: `marca-consultoria/site-2026/prototipo-v2/`.

## Publicação

O deploy é automático via **Publicação via Git** da KingHost: cada `push` na
branch `master` sincroniza os arquivos para a hospedagem. Não há passo de build.

Fluxo de edição:
1. Editar o HTML da página.
2. `git add`, `git commit`, `git push origin master`.
3. A KingHost sincroniza sozinha. Sem "Republish" manual.

## Estrutura

| Arquivo               | URL no ar        |
|-----------------------|------------------|
| `index.html`          | `/`              |
| `metodo.html`         | `/metodo`        |
| `plano-exemplo.html`  | `/plano-exemplo` |
| `sobre.html`          | `/sobre`         |
| `cartas.html`         | `/cartas`        |
| `conversa.html`       | `/conversa`      |
| `presente.html`       | `/presente`      |
| `privacidade.html`    | `/privacidade`   |
| `termos.html`         | `/termos`        |
| `foto-leo.webp`       | asset (hero /sobre) |
| `.htaccess`           | URLs limpas + HTTPS + cache |

URLs limpas (`/metodo` em vez de `/metodo.html`) são geridas pelo `.htaccess`.
