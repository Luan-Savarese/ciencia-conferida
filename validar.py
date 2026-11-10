#!/usr/bin/env python3
"""Valida artigos: o site só é gerado se todos passarem.

Uso:  python3 validar.py                       (todos em artigos/)
      python3 validar.py rascunhos/x.md ...    (arquivos específicos)

Regras (as mesmas da página "Como fazemos"):
- cabeçalho completo; nome do arquivo AAAA-MM-DD-slug.md igual ao slug e à data de publicação
- pelo menos 2 fontes, https, de pelo menos 2 sites diferentes, cada uma com data de conferência
- tema (campo "categoria") entre os 6 do site e "nivel" (iniciante, intermediario ou avancado)
- 1 a 3 linhas "curiosidade:": cada uma é uma frase copiada do texto do artigo, terminada por [n] de fonte que existe
- seções "Resposta rápida" (até 60 palavras), "Explicando melhor" e "O que ainda não se sabe" ("Para ir mais fundo" é opcional)
- todo parágrafo ou item com algum número leva citação [n]; toda citação aponta para uma fonte que existe; toda fonte é citada
- nada de marcas de rascunho (TODO, XXX, lorem, ???)
- noticias.json: só links https de sites de uma lista aprovada, com data de publicação e fonte, resumo curto, tema válido
"""
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
from build import ler_artigo, sem_marcas  # noqa: E402
import visual  # noqa: E402

CATEGORIAS = set(visual.TEMAS)
NIVEIS = {"iniciante", "intermediario", "avancado"}
OBRIGATORIOS = ["titulo", "slug", "categoria", "nivel", "publicado", "conferido", "resumo"]
# sites aprovados para notícias (o endereço precisa terminar num destes nomes)
DOMINIOS_NOTICIAS = {
    "nasa.gov", "noaa.gov", "esa.int", "usgs.gov", "nih.gov", "who.int", "cern.ch", "home.cern", "si.edu",
    "fapesp.br", "usp.br", "unicamp.br", "unesp.br", "ufmg.br", "ufrj.br", "ufscar.br", "fiocruz.br", "inpe.br", "embrapa.br",
    "butantan.gov.br", "agenciabrasil.ebc.com.br", "gov.br",
    "g1.globo.com", "oglobo.globo.com", "cnnbrasil.com.br", "bbc.com", "uol.com.br", "estadao.com.br",
    "nature.com", "science.org", "scientificamerican.com", "nationalgeographic.com", "smithsonianmag.com",
}
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
    if a["nivel"] not in NIVEIS:
        erros.append(f"nivel '{a['nivel']}' deve ser um de {sorted(NIVEIS)}")
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
    # curiosidades: frases do próprio artigo, com fonte
    cur = a["curiosidades"]
    if not 1 <= len(cur) <= 3:
        erros.append("precisa de 1 a 3 linhas 'curiosidade:'")
    corpo_limpo = sem_marcas(corpo)
    for c in cur:
        marcas = [int(x) for x in re.findall(r"\[(\d+)\]", c)]
        if not marcas or not re.search(r"\[\d+\]\s*$", c):
            erros.append(f"curiosidade sem [n] no fim: «{c[:60]}…»")
        for n in marcas:
            if n < 1 or n > len(fontes):
                erros.append(f"curiosidade cita [{n}], fonte que não existe")
        txt = sem_marcas(c)
        if len(txt) > 280:
            erros.append(f"curiosidade passa de 280 caracteres: «{c[:60]}…»")
        if txt not in corpo_limpo:
            erros.append(f"curiosidade não está no texto do artigo (copie a frase como está): «{c[:60]}…»")
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


def valida_noticias():
    arq = RAIZ / "noticias.json"
    if not arq.exists():
        return []
    try:
        itens = json.loads(arq.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"noticias.json inválido: {e}"]
    erros, vistas = [], set()
    hoje = date.today()
    for i, n in enumerate(itens, 1):
        pre = f"notícia {i}"
        for k in ("titulo", "resumo", "fonte", "url", "publicado", "coletado", "tema"):
            if not n.get(k):
                erros.append(f"{pre}: falta '{k}'")
        if any(not n.get(k) for k in ("titulo", "resumo", "fonte", "url", "publicado", "coletado", "tema")):
            continue
        u = urlparse(n["url"])
        host = (u.hostname or "").lower()
        if u.scheme != "https" or not host:
            erros.append(f"{pre}: o link deve ser https")
        elif not any(host == d or host.endswith("." + d) for d in DOMINIOS_NOTICIAS):
            erros.append(f"{pre}: site '{host}' não está na lista aprovada (DOMINIOS_NOTICIAS)")
        if n["url"] in vistas:
            erros.append(f"{pre}: link repetido")
        vistas.add(n["url"])
        if n["tema"] not in CATEGORIAS:
            erros.append(f"{pre}: tema '{n['tema']}' não está em {sorted(CATEGORIAS)}")
        pub, col = iso(n["publicado"]), iso(n["coletado"])
        if not pub or not col:
            erros.append(f"{pre}: datas devem ser AAAA-MM-DD")
        else:
            if pub > hoje or col > hoje:
                erros.append(f"{pre}: data no futuro")
            if col < pub:
                erros.append(f"{pre}: 'coletado' anterior a 'publicado'")
        if len(n["titulo"]) > 120:
            erros.append(f"{pre}: título passa de 120 caracteres")
        if len(n["resumo"]) > 340:
            erros.append(f"{pre}: resumo passa de 340 caracteres")
        if PALAVRAS_PROIBIDAS.search(n["titulo"] + " " + n["resumo"]):
            erros.append(f"{pre}: marca de rascunho")
    return erros


def main():
    alvos = [Path(p) for p in sys.argv[1:]] or sorted((RAIZ / "artigos").glob("*.md"))
    problemas = 0
    if not sys.argv[1:]:
        e = valida_noticias()
        print(("OK   " if not e else "ERRO ") + "noticias.json")
        for x in e:
            print("       -", x)
        problemas += len(e)
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
