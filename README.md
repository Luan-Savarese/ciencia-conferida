# Ciência Conferida

Ciência com fonte em cada fato: respostas curtas e explicações completas para curiosos de 8 a 80 anos. Site estático, grátis, publicado pelo GitHub Pages a partir da pasta `docs/`.

**Site:** https://luan-savarese.github.io/ciencia-conferida/

## O que tem no site
Início (destaque, curiosidade do dia, notícias, curiosidades, temas, filtros), 6 temas (Espaço, Animais, Corpo humano, Tecnologia, Meio ambiente, Física), Notícias, Busca (com filtros de tema e nível), Salvos (guardados só no navegador), compartilhar (Web Share, copiar link, WhatsApp) e dois feeds RSS (`feed.xml` com os artigos, `noticias.xml` com as notícias). Sem pop-ups e sem cadastro. O JavaScript (`assets/app.js`) é opcional: sem ele o site continua legível.

## Como cada artigo nasce
1. O **Redator** escreve um rascunho por dia em `rascunhos/`, com pelo menos 2 fontes institucionais abertas e lidas (`equipe/ROTINA-REDATOR.md`).
2. O **Conferente**, em outra sessão, reabre todas as fontes, confere cada frase e só então move o artigo para `artigos/` e gera o site (`equipe/ROTINA-CONFERENTE.md`). Rascunho que não passa vai para `rascunhos/reprovados/`.
3. `python3 build.py` valida (`validar.py`) e gera `docs/`. O validador recusa artigo com menos de 2 fontes, número sem citação `[n]` ou sem as seções "Resposta rápida", "Explicando melhor" e "O que ainda não se sabe".
4. Erro achado depois: corrige, e anota em `correcoes.json` (aparece na página Correções).

## Notícias
O **Repórter** (`equipe/ROTINA-REPORTER.md`) acrescenta todo dia, em `noticias.json`, resumos curtos de reportagens de fontes aprovadas (lista `DOMINIOS_NOTICIAS` em `validar.py`), sempre com data, fonte e link. Elas **não** têm a conferência completa dos artigos, e o site diz isso. O Conferente confere 3 por dia.

## Arquivos
- `artigos/AAAA-MM-DD-slug.md`: artigos publicados (cabeçalho com título, `categoria` (tema), `nivel`, datas, resumo, `fonte:` e `curiosidade:`; corpo em markdown simples).
- `noticias.json`: notícias do dia. `assets/estilo.css` e `assets/app.js`: visual e interações. `visual.py`: ilustrações e temas.
- `rascunhos/`: aguardando o Conferente. `equipe/temas.md`: fila de temas. `equipe/registro.md`: diário.
- `site.json`: nome, endereço e medição de visitas. `build.py`, `validar.py`: o gerador e o validador (só biblioteca padrão do Python).

## Medir as visitas (analytics)
O GitHub Pages não conta visitas. Para ligar a medição, crie uma conta grátis no GoatCounter (sem cookies, não precisa de aviso de cookies), escolha um código e coloque em `site.json`:

```json
"analytics": { "tipo": "goatcounter", "codigo": "seu-codigo" }
```

Depois rode `python3 build.py` e faça commit. (Também há suporte a `"tipo": "ga4"` com `"codigo": "G-XXXXXXX"`, mas o Google Analytics usa cookies e pede aviso de privacidade.)

## Gerar o site na sua máquina
```
python3 validar.py
python3 build.py
python3 -m http.server 8000 --directory docs
```
