# Ciência Conferida

Ciência com fonte em cada fato: respostas curtas e explicações completas para curiosos de 8 a 80 anos. Site estático, grátis, publicado pelo GitHub Pages a partir da pasta `docs/`.

**Site:** https://luan-savarese.github.io/ciencia-conferida/

## Como cada artigo nasce
1. O **Redator** escreve um rascunho por dia em `rascunhos/`, com pelo menos 2 fontes institucionais abertas e lidas (`equipe/ROTINA-REDATOR.md`).
2. O **Conferente**, em outra sessão, reabre todas as fontes, confere cada frase e só então move o artigo para `artigos/` e gera o site (`equipe/ROTINA-CONFERENTE.md`). Rascunho que não passa vai para `rascunhos/reprovados/`.
3. `python3 build.py` valida (`validar.py`) e gera `docs/`. O validador recusa artigo com menos de 2 fontes, número sem citação `[n]` ou sem as seções "Resposta rápida", "Explicando melhor" e "O que ainda não se sabe".
4. Erro achado depois: corrige, e anota em `correcoes.json` (aparece na página Correções).

## Arquivos
- `artigos/AAAA-MM-DD-slug.md`: artigos publicados (cabeçalho com título, categoria, datas, resumo e `fonte:`; corpo em markdown simples).
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
