#!/usr/bin/env python3
"""Valida artigos: o site só é gerado se todos passarem.

Uso:  python3 validar.py                       (todos em artigos/)
      python3 validar.py rascunhos/x.md ...    (arquivos específicos)

Regras (as mesmas da página "Como fazemos"):
- cabeçalho completo; nome do arquivo AAAA-MM-DD-slug.md igual ao slug e à data de publicação
- pelo menos 2 fontes, https, de pelo menos 2 sites diferentes, cada uma com data de conferência
- seções "Resposta rápida" (até 60 palavras), "Explicando melhor" e "O que ainda não se sabe"
- todo parágrafo ou item com algum número leva citação [n]; toda citação aponta para uma fonte que existe; toda fonte é citada
- nada de marcas de rascunho (TODO, XXX, lorem, ???)
"""
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
from build import ler_artigo  # noqa: E402

CATEGORIAS = {"Terra e céu", "Espaço", "Corpo humano", "Vida", "Matéria e energia", "Tecnologia", "Mente e comportamento"}
OBRIGATORIOS = ["titulo", "slug", "categoria", "publicado", "conferido", "resumo"]
PALAVRAS_PROIBIDAS = re.compile(r"\b(TODO|XXX)\b|\b(?i:lorem|ipsum)\b|\?\?\?")  # TODO só em maiúsculas: "todo" é português


def iso(s):
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def valida(caminho):
    erros = []
    try:
        a = ler_artigo(caminho)
    except ValueError as e:
        return [str(e)]
    for k in OBRIGATORIOS:
        if not a.get(k):
            erros.append(f"falta o campo '{k}'")
    if erros:
        return erros
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md", caminho.name)
    if not m:
        erros.append("nome do arquivo deve ser AAAA-MM-DD-slug.md")
    else:
        if m.group(2) != a["slug"]:
            erros.append(f"slug '{a['slug']}' difere do nome do arquivo")
        if m.group(1) != a["publicado"]:
            erros.append("data do nome do arquivo difere de 'publicado'")
    if a["categoria"] not in CATEGORIAS:
        erros.append(f"categoria '{a['categoria']}' não está em {sorted(CATEGORIAS)}")
    pub, conf = iso(a["publicado"]), iso(a["conferido"])
    if not pub or not conf:
        erros.append("'publicado' e 'conferido' devem ser AAAA-MM-DD")
    elif conf < pub:
        erros.append("'conferido' não pode ser anterior a 'publicado'")
    if len(a["resumo"]) > 200:
        erros.append("resumo passa de 200 caracteres")
    fontes = a["fontes"]
    if len(fontes) < 2:
        erros.append("precisa de pelo menos 2 fontes")
    sites = set()
    for i, f in enumerate(fontes, 1):
        u = urlparse(f["url"])
        if u.scheme != "https" or not u.netloc:
            erros.append(f"fonte {i}: o link deve ser https")
        sites.add(u.netloc.lower().removeprefix("www."))
        if not iso(f["acessado"]):
            erros.append(f"fonte {i}: data de conferência inválida")
    if len(fontes) >= 2 and len(sites) < 2:
        erros.append("as fontes devem ser de pelo menos 2 sites diferentes")
    corpo = a["corpo"]
    if PALAVRAS_PROIBIDAS.search(corpo) or PALAVRAS_PROIBIDAS.search(a["resumo"]):
        erros.append("há marca de rascunho (TODO, XXX, lorem ou ???)")
    titulos = re.findall(r"(?m)^## (.+)$", corpo)
    baixos = [t.lower() for t in titulos]
    for exigido in ("resposta rápida", "explicando melhor", "o que ainda"):
        if not any(t.startswith(exigido) for t in baixos):
            erros.append(f"falta a seção '## {exigido.capitalize()}…'")
    # resposta rápida curta
    m2 = re.search(r"(?ms)^## Resposta rápida\n(.*?)(?=^## |\Z)", corpo)
    if m2 and len(re.findall(r"\w+", re.sub(r"\[\d+\]", "", m2.group(1)))) > 60:
        erros.append("a resposta rápida passa de 60 palavras")
    # citações
    citadas = set()
    for bloco in re.split(r"\n\s*\n", corpo):
        t = bloco.strip()
        if not t or t.startswith("#"):
            continue
        marcas = [int(x) for x in re.findall(r"\[(\d+)\](?!\()", t)]
        citadas.update(marcas)
        for n in marcas:
            if n < 1 or n > len(fontes):
                erros.append(f"citação [{n}] aponta para fonte que não existe")
        sem_marca = re.sub(r"\[\d+\](?!\()", "", t)
        sem_marca = re.sub(r"\]\([^)]*\)", "]", sem_marca)  # ignora números dentro de links
        if re.search(r"\d", sem_marca) and not marcas:
            erros.append(f"número sem citação [n]: «{t[:70]}…»")
    for i in range(1, len(fontes) + 1):
        if i not in citadas:
            erros.append(f"a fonte {i} nunca é citada no texto")
    return erros


def main():
    alvos = [Path(p) for p in sys.argv[1:]] or sorted((RAIZ / "artigos").glob("*.md"))
    problemas = 0
    for p in alvos:
        e = valida(p)
        print(("OK   " if not e else "ERRO ") + p.name)
        for x in e:
            print("       -", x)
        problemas += len(e)
    print("total de problemas:", problemas)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
