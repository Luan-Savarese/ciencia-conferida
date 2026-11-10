#!/usr/bin/env python3
"""Gera o site (pasta docs/) a partir de artigos/*.md, noticias.json e site.json. Só biblioteca padrão.

Uso:  python3 build.py            (valida e gera)
      python3 build.py --sem-validar
"""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
import visual  # noqa: E402
SAIDA = RAIZ / "docs"
CFG = json.loads((RAIZ / "site.json").read_text(encoding="utf-8"))
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]
NIVEIS = {"iniciante": "Iniciante", "intermediario": "Intermediário", "avancado": "Avançado"}
NIVEL_DESC = {"iniciante": "Para quem está começando: sem termos difíceis, tudo explicado do zero.",
              "intermediario": "Para quem já conhece o básico e quer entender o porquê.",
              "avancado": "Para quem quer ir fundo, com termos técnicos e mais detalhes."}
BASE = CFG["url"].rstrip("/") + "/"
ICO_SALVAR = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>')
ICO_COMPART = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
               'stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3M8 7l4-4 4 4M5 12v8h14v-8"/></svg>')
ICO_ZAP = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.7 7L4 20l1.1-4.9A8 8 0 1 1 21 12z"/></svg>')
_uid_n = [0]


def uid():
    _uid_n[0] += 1
    return f"u{_uid_n[0]}"


# ---------- utilidades ----------
def data_br(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def data_curta(iso):
    d = date.fromisoformat(iso)
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def esc(s):
    return html.escape(str(s), quote=True)


def slug_titulo(s):
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")


def sem_marcas(s):
    """Texto sem as marcas [n] de fonte e com espaços normalizados (usado para comparar frases)."""
    return re.sub(r"\s+", " ", re.sub(r"\[\d+\](?!\()", "", s)).strip()


def minutos(corpo):
    return max(1, round(len(re.findall(r"\w+", sem_marcas(corpo))) / 190))


def ler_artigo(caminho):
    """Lê um artigo .md: cabeçalho entre '---' e corpo em markdown simples."""
    texto = caminho.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)\Z", texto, re.S)
    if not m:
        raise ValueError(f"{caminho.name}: sem cabeçalho '---'")
    cab, corpo = m.groups()
    meta = {"fontes": [], "curiosidades": [], "arquivo": caminho.name}
    for linha in cab.split("\n"):
        if not linha.strip():
            continue
        k, _, v = linha.partition(":")
        k, v = k.strip(), v.strip()
        if k == "fonte":
            p = [x.strip() for x in v.split(" | ")]
            if len(p) != 4:
                raise ValueError(f"{caminho.name}: fonte deve ter 4 partes (título | instituição | url | acessado em)")
            meta["fontes"].append({"titulo": p[0], "instituicao": p[1], "url": p[2], "acessado": p[3]})
        elif k == "curiosidade":
            meta["curiosidades"].append(v)
        else:
            meta[k] = v
    meta["corpo"] = corpo.strip()
    return meta


def ler_noticias():
    arq = RAIZ / "noticias.json"
    itens = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else []
    itens.sort(key=lambda n: (n["publicado"], n.get("coletado", "")), reverse=True)
    return itens


# ---------- markdown simples ----------
def inline(s, rel_fontes=""):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]\[]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\[(\d+)\]", rf'<sup class="cit"><a href="{rel_fontes}#fonte-\1" aria-label="Fonte \1">[\1]</a></sup>', s)
    return s


def blocos(texto, heads):
    """Converte um trecho de markdown (sem títulos ##) em HTML. Os títulos ### entram em `heads` (para o índice)."""
    saida, par, lista, cit = [], [], [], []

    def fecha():
        nonlocal par, lista, cit
        if par:
            saida.append("<p>" + inline(" ".join(par)) + "</p>")
        if lista:
            saida.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in lista) + "</ul>")
        if cit:
            saida.append("<blockquote><p>" + inline(" ".join(cit)) + "</p></blockquote>")
        par, lista, cit = [], [], []

    for linha in texto.split("\n"):
        t = linha.strip()
        if not t:
            fecha()
        elif t.startswith("### "):
            fecha()
            base = slug_titulo(t[4:]) or "secao"
            hid, n = base, 2
            while any(h[0] == hid for h in heads):
                hid, n = f"{base}-{n}", n + 1
            heads.append((hid, re.sub(r"\[\d+\]", "", t[4:]).strip(), "h3"))
            saida.append(f'<h3 id="{hid}">{inline(t[4:])}</h3>')
        elif t.startswith("- "):
            if par or cit:
                fecha()
            lista.append(t[2:])
        elif t.startswith("> "):
            if par or lista:
                fecha()
            cit.append(t[2:])
        else:
            if lista or cit:
                fecha()
            par.append(t)
    fecha()
    return "\n".join(saida)


def corpo_html(meta):
    """Divide o corpo nas seções '## ' e devolve (HTML, índice)."""
    partes = re.split(r"(?m)^## ", "\n" + meta["corpo"])
    secoes, heads = [], []
    for p in partes[1:]:
        titulo, _, resto = p.partition("\n")
        titulo = titulo.strip()
        low = titulo.lower()
        cls = "secao"
        if low.startswith("resposta rápida"):
            cls = "secao resposta"
        elif low.startswith("o que ainda"):
            cls = "secao ainda"
        elif low.startswith("para ir mais fundo"):
            cls = "secao fundo"
        sid = slug_titulo(titulo)
        heads.append((sid, titulo, "h2"))
        secoes.append(f'<section class="{cls}" id="{sid}"><h2>{inline(titulo)}</h2>\n{blocos(resto, heads)}</section>')
    return "\n".join(secoes), heads


# ---------- estilo e script (arquivos em assets/) ----------
CSS = (RAIZ / "assets" / "estilo.css").read_text(encoding="utf-8")
JS = (RAIZ / "assets" / "app.js").read_text(encoding="utf-8")
CSS_V = hashlib.md5(CSS.encode("utf-8")).hexdigest()[:8]  # muda quando o visual muda: o navegador não usa arquivo velho
JS_V = hashlib.md5(JS.encode("utf-8")).hexdigest()[:8]


def analytics_html():
    a = CFG.get("analytics") or {}
    tipo, cod = (a.get("tipo") or "").strip().lower(), (a.get("codigo") or "").strip()
    if not tipo or not cod:
        return ""
    if tipo == "goatcounter" and re.fullmatch(r"[a-z0-9-]+", cod):
        return (f'<script data-goatcounter="https://{cod}.goatcounter.com/count" async '
                f'src="//gc.zgo.at/count.js"></script>')
    if tipo == "ga4" and re.fullmatch(r"G-[A-Z0-9]+", cod):
        return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={cod}"></script>'
                f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}"
                f"gtag('js',new Date());gtag('config','{cod}');</script>")
    return ""


def escreve(rel_path, conteudo):
    p = SAIDA / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(conteudo, encoding="utf-8")


def pagina(titulo, desc, corpo, rel, url_rel, ativo="", og_tipo="website", jsonld=None, noindex=False):
    nome = CFG["nome"]
    t = nome if titulo == nome else f"{titulo} · {nome}"
    canon = BASE + url_rel
    menu = [("", "Início", "inicio"), ("noticias/", "Notícias", "noticias"), ("#temas", "Temas", "temas"),
            ("buscar/", "Buscar", "buscar"), ("salvos/", "Salvos", "salvos"), ("como-fazemos/", "Como fazemos", "como")]
    itens = []
    for u, n, k in menu:
        cur = ' aria-current="page"' if k == ativo else ""
        extra = ' <span class="cnt" id="cont-salvos" hidden>0</span>' if k == "salvos" else ""
        itens.append(f'<a href="{rel}{u}"{cur}>{n}{extra}</a>')
    nav = "".join(itens)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    temas_rod = "".join(f'<li><a href="{rel}tema/{s}/">{esc(n)}</a></li>' for n, (s, _, _) in visual.TEMAS.items())
    return f"""<!doctype html>
<html lang="{CFG['idioma']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(t)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:title" content="{esc(t)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{og_tipo}">
<meta property="og:url" content="{esc(canon)}">
<meta property="og:locale" content="pt_BR">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#060c1d">
{robots}
<link rel="alternate" type="application/rss+xml" title="{esc(nome)}: artigos" href="{rel}feed.xml">
<link rel="alternate" type="application/rss+xml" title="{esc(nome)}: notícias de ciência" href="{rel}noticias.xml">
<link rel="preload" href="{rel}fontes/fraunces-600.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{rel}estilo.css?v={CSS_V}">
{ld}
{analytics_html()}
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="top"><div class="in"><a class="logo" href="{rel or './'}">{visual.marca()}<span>{esc(nome)}<small>ciência com fonte</small></span></a><nav class="menu" aria-label="Principal">{nav}</nav></div></header>
<main id="conteudo">
{corpo}
</main>
<footer class="pe"><div class="in">
<div><strong>{esc(nome)}</strong><p>{esc(CFG['slogan'])}. Os textos são escritos com ajuda de inteligência artificial e conferidos contra as fontes citadas em cada artigo
(<a href="{rel}como-fazemos/">como fazemos</a>). Viu algum erro? <a href="{esc(CFG['repo'])}/issues/new">Avise aqui</a>: corrigimos e registramos em <a href="{rel}correcoes/">correções</a>.</p></div>
<div><h2>Temas</h2><ul>{temas_rod}</ul></div>
<div><h2>O site</h2><ul><li><a href="{rel}noticias/">Notícias de ciência</a></li><li><a href="{rel}buscar/">Buscar</a></li><li><a href="{rel}salvos/">Salvos</a></li><li><a href="{rel}como-fazemos/">Como fazemos</a></li><li><a href="{rel}correcoes/">Correções</a></li><li><a href="{rel}sobre/">Sobre</a></li><li><a href="{rel}feed.xml">Receber por RSS</a></li></ul></div>
</div></footer>
<div id="aviso" role="status" aria-live="polite"></div>
<script src="{rel}app.js?v={JS_V}" defer></script>
</body>
</html>
"""


# ---------- peças reutilizáveis ----------
def botao_salvar(a, mini=False):
    return (f'<button class="mini salvar" type="button" data-slug="{esc(a["slug"])}" data-titulo="{esc(a["titulo"])}" '
            f'aria-pressed="false" hidden>{ICO_SALVAR}<span>Salvar</span></button>')


def cartao(a, rel):
    sc = visual.slug_tema(a["categoria"])
    href = f'{rel}artigos/{a["slug"]}/'
    return (f'<article class="card t-{sc}" data-tema="{sc}" data-nivel="{a["nivel"]}">'
            f'<a class="thumb" href="{href}" tabindex="-1" aria-hidden="true">{visual.cena(a["categoria"], uid())}</a>'
            f'{botao_salvar(a)}'
            f'<div class="cb"><div class="tags"><span class="chip">{esc(a["categoria"])}</span><span class="chip nv">{NIVEIS[a["nivel"]]}</span></div>'
            f'<h3><a href="{href}">{esc(a["titulo"])}</a></h3><p>{esc(a["resumo"])}</p>'
            f'<div class="rod"><span class="selo"><i aria-hidden="true">✓</i>Conferido em {data_curta(a["conferido"])}</span>'
            f'<span>{minutos(a["corpo"])} min de leitura</span></div></div></article>')


def cartao_noticia(n):
    sc = visual.slug_tema(n["tema"])
    return (f'<article class="card noticia t-{sc}"><div class="cb">'
            f'<span class="tipo">Notícia · resumo de reportagem de terceiros</span>'
            f'<div class="fonte-linha">{esc(n["fonte"])} · publicada em {data_curta(n["publicado"])}</div>'
            f'<h3><a href="{esc(n["url"])}" rel="noopener">{esc(n["titulo"])}</a></h3><p>{esc(n["resumo"])}</p>'
            f'<div class="tags"><span class="chip">{esc(n["tema"])}</span></div>'
            f'<span class="ext">Ler na fonte ↗</span></div></article>')


NOTA_NOTICIAS = ("Estes resumos são escritos pela nossa equipe a partir de notícias publicadas por instituições e veículos de confiança, "
                 "com a data e a fonte ao lado. Eles <strong>não passam pela conferência completa dos artigos</strong> "
                 "(não reabrimos todos os dados): para os detalhes, abra sempre a fonte.")


def curiosidade_html(c, rel):
    """Texto da curiosidade com as marcas [n] apontando para a fonte dentro do artigo."""
    return inline(c["texto"], rel_fontes=f'{rel}artigos/{c["slug"]}/')


def lista_curiosidades(arts):
    out = []
    for a in arts:
        for txt in a["curiosidades"]:
            out.append({"texto": txt, "slug": a["slug"], "titulo": a["titulo"], "tema": a["categoria"]})
    return out


def relacionados(a, arts, n=3):
    def palavras(x):
        return {w for w in re.findall(r"\w{5,}", (x["titulo"] + " " + x["resumo"]).lower())}
    base = palavras(a)
    pont = []
    for b in arts:
        if b["slug"] == a["slug"]:
            continue
        s = (3 if b["categoria"] == a["categoria"] else 0) + len(base & palavras(b)) + (1 if b["nivel"] == a["nivel"] else 0)
        pont.append((s, b["publicado"], b))
    pont.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [b for _, _, b in pont[:n]]


# ---------- páginas ----------
def pagina_artigo(a, arts):
    sc = visual.slug_tema(a["categoria"])
    fontes = "".join(
        f'<li id="fonte-{i}"><a href="{esc(f["url"])}" rel="noopener">{esc(f["titulo"])}</a>'
        f'<span class="inst">{esc(f["instituicao"])} · aberta e conferida em {data_curta(f["acessado"])}</span></li>'
        for i, f in enumerate(a["fontes"], 1))
    miolo, heads = corpo_html(a)
    # índice: cada título ## com seus ### dentro
    grupos = []
    for hid, txt, nivel in heads:
        if nivel == "h2":
            grupos.append((hid, txt, []))
        elif grupos:
            grupos[-1][2].append((hid, txt))
    itens = []
    for hid, txt, filhos in grupos:
        sub = ("<ol>" + "".join(f'<li><a href="#{h}">{esc(t)}</a></li>' for h, t in filhos) + "</ol>") if filhos else ""
        itens.append(f'<li><a href="#{hid}">{esc(txt)}</a>{sub}</li>')
    itens.append('<li><a href="#fontes">Fontes</a></li>')
    toc = f'<nav class="toc" aria-label="Neste artigo"><h2>Neste artigo</h2><ol>{"".join(itens)}</ol></nav>'
    url_abs = f'{BASE}artigos/{a["slug"]}/'
    zap = f'https://wa.me/?text={esc(quote(a["titulo"] + " " + url_abs))}'
    rel_cards = "".join(cartao(b, "../../") for b in relacionados(a, arts))
    rel_sec = (f'<section class="rel"><div class="titulo-bloco"><h2>Continue explorando</h2><a class="mais" href="../../tema/{sc}/">Mais em {esc(a["categoria"])}</a></div>'
               f'<div class="grade">{rel_cards}</div></section>') if rel_cards else ""
    corpo = f"""<div class="in t-{sc}">
<div class="banner">{visual.cena(a['categoria'], uid())}</div>
<header class="ahead">
<div class="tags"><a class="chip" href="../../tema/{sc}/">{esc(a['categoria'])}</a><span class="chip nv" title="{esc(NIVEL_DESC[a['nivel']])}">{NIVEIS[a['nivel']]}</span></div>
<h1>{esc(a['titulo'])}</h1>
<p class="lead">{esc(a['resumo'])}</p>
<p class="meta"><span class="selo"><i aria-hidden="true">✓</i>Conferido em {data_br(a['conferido'])}</span><span>Publicado em {data_br(a['publicado'])}</span><span>{minutos(a['corpo'])} min de leitura</span></p>
<div class="barra">{botao_salvar(a)}<button class="mini compartilhar" type="button" data-url="{esc(url_abs)}" data-titulo="{esc(a['titulo'])}" hidden>{ICO_COMPART}<span>Compartilhar</span></button><a class="mini" href="{zap}" rel="noopener">{ICO_ZAP}<span>WhatsApp</span></a></div>
</header>
<div class="corpo-art">
{toc}
<article>
{miolo}
<section class="fontes" id="fontes"><h2>Fontes</h2><ol>{fontes}</ol></section>
<p class="erro">Cada fato acima leva o número da fonte em que foi conferido. Se você achar algo errado ou desatualizado,
<a href="{esc(CFG['repo'])}/issues/new">avise aqui</a>: a gente corrige e anota na página de <a href="../../correcoes/">correções</a>.</p>
</article>
</div>
{rel_sec}
</div>"""
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["titulo"], "inLanguage": "pt-BR",
          "datePublished": a["publicado"], "dateModified": a["conferido"], "description": a["resumo"],
          "about": a["categoria"], "timeRequired": f"PT{minutos(a['corpo'])}M",
          "publisher": {"@type": "Organization", "name": CFG["nome"]},
          "citation": [f["url"] for f in a["fontes"]]}
    escreve(f"artigos/{a['slug']}/index.html",
            pagina(a["titulo"], a["resumo"], corpo, "../../", f"artigos/{a['slug']}/", og_tipo="article", jsonld=ld))


def tiles_temas(arts, rel):
    out = []
    for nome, (s, desc, _) in visual.TEMAS.items():
        n = sum(1 for a in arts if a["categoria"] == nome)
        cont = f"{n} artigo" + ("" if n == 1 else "s") if n else "em breve"
        out.append(f'<article class="tema t-{s}"><div class="thumb" aria-hidden="true">{visual.cena(nome, uid())}</div>'
                   f'<div class="cb"><h3><a href="{rel}tema/{s}/">{esc(nome)}</a></h3><p>{esc(desc)}</p><span class="n">{cont}</span></div></article>')
    return "".join(out)


def pagina_inicio(arts, noticias):
    cur = lista_curiosidades(arts)
    destaque = arts[0] if arts else None
    if destaque:
        sc = visual.slug_tema(destaque["categoria"])
        href = f'artigos/{destaque["slug"]}/'
        hero_txt = (f'<p class="kicker">Em destaque</p><div class="tags"><span class="chip">{esc(destaque["categoria"])}</span>'
                    f' <span class="chip nv">{NIVEIS[destaque["nivel"]]}</span></div>'
                    f'<h1><a href="{href}">{esc(destaque["titulo"])}</a></h1><p class="lead">{esc(destaque["resumo"])}</p>'
                    f'<p class="meta"><span class="selo"><i aria-hidden="true">✓</i>Conferido em {data_curta(destaque["conferido"])}</span>'
                    f'<span>{minutos(destaque["corpo"])} min de leitura</span></p>'
                    f'<div class="acoes"><a class="btn" href="{href}">Ler agora</a><a class="btn sec" href="#temas">Explorar por tema</a></div>')
        hero_art = f'<a class="vitrine" href="{href}" tabindex="-1" aria-hidden="true">{visual.cena(destaque["categoria"], uid())}</a>'
        cls_hero = f"t-{sc}"
    else:
        hero_txt = (f'<p class="kicker">Para curiosos de 8 a 80 anos</p><h1>{esc(CFG["slogan"])}</h1><p class="lead">{esc(CFG["descricao"])}</p>')
        hero_art, cls_hero = "", ""
    # curiosidade do dia (a mesma conta é refeita no navegador com a data de quem lê)
    dia = ""
    if cur:
        i = (date.today().toordinal() - date(1970, 1, 1).toordinal()) % len(cur)
        c = cur[i]
        lista_js = [{"html": curiosidade_html(x, ""), "url": f'artigos/{x["slug"]}/',
                     "rodape": f'Do artigo <a href="artigos/{esc(x["slug"])}/">{esc(x["titulo"])}</a>'} for x in cur]
        dados = json.dumps(lista_js, ensure_ascii=False).replace("</", "<\\/")
        dia = (f'<section class="faixa in" aria-labelledby="t-dia"><div class="dia" id="dia"><div class="ic" aria-hidden="true">?!</div><div>'
               f'<h2 id="t-dia">Curiosidade do dia</h2><blockquote id="dia-texto">{curiosidade_html(c, "")}</blockquote>'
               f'<p class="rod" id="dia-rodape">Do artigo <a href="artigos/{esc(c["slug"])}/">{esc(c["titulo"])}</a></p></div></div>'
               f'<script type="application/json" id="dados-curiosidades">{dados}</script></section>')
    # notícias
    noticias_sec = ""
    if noticias:
        cards = "".join(cartao_noticia(n) for n in noticias[:3])
        noticias_sec = (f'<section class="faixa in" id="noticias" aria-labelledby="t-not"><div class="titulo-bloco"><div><h2 id="t-not">Notícias de ciência</h2>'
                        f'<p>As novidades mais recentes, com data e fonte à vista.</p></div><a class="mais" href="noticias/">Ver todas</a></div>'
                        f'<div class="grade">{cards}</div><p class="nota-fonte">{NOTA_NOTICIAS}</p></section>')
    # curiosidades rápidas
    curios_sec = ""
    if cur:
        cards = "".join(
            f'<article class="curio t-{visual.slug_tema(x["tema"])}"><span class="chip">{esc(x["tema"])}</span><p>{curiosidade_html(x, "")}</p>'
            f'<span class="rod"><a href="artigos/{esc(x["slug"])}/">Ler: {esc(x["titulo"])}</a></span></article>'
            for x in cur[:8])
        curios_sec = (f'<section class="faixa in" id="curiosidades" aria-labelledby="t-cur"><div class="titulo-bloco"><div><h2 id="t-cur">Curiosidades rápidas</h2>'
                      f'<p>Fatos curtos tirados dos artigos, cada um com o número da fonte.</p></div></div><div class="curios">{cards}</div></section>')
    # comece por aqui
    iniciantes = [a for a in arts if a["nivel"] == "iniciante" and a is not destaque][:3]
    comece = ""
    if iniciantes:
        comece = (f'<section class="faixa in" aria-labelledby="t-com"><div class="titulo-bloco"><div><h2 id="t-com">Comece por aqui</h2>'
                  f'<p>{esc(NIVEL_DESC["iniciante"])}</p></div></div><div class="grade">{"".join(cartao(a, "") for a in iniciantes)}</div></section>')
    temas_presentes = [n for n in visual.ORDEM if any(a["categoria"] == n for a in arts)]
    niveis_presentes = [k for k in NIVEIS if any(a["nivel"] == k for a in arts)]
    filtros = ""
    if len(arts) > 1:
        bt = "".join(f'<button type="button" data-tipo="tema" data-valor="{visual.slug_tema(n)}" aria-pressed="false">{esc(n)}</button>' for n in temas_presentes)
        bn = "".join(f'<button type="button" data-tipo="nivel" data-valor="{k}" aria-pressed="false">{NIVEIS[k]}</button>' for k in niveis_presentes)
        filtros = f'<div class="filtros" id="filtros" role="group" aria-label="Filtrar artigos" hidden>{bt}{bn}</div>'
    todos = "\n".join(cartao(a, "") for a in arts) or '<p class="vazio">Os primeiros artigos chegam em breve.</p>'
    corpo = f"""<section class="hero {cls_hero}"><div class="in"><div>{hero_txt}</div>{hero_art}</div></section>
<section class="faixa in" aria-label="Buscar"><form class="busca" role="search" action="buscar/" method="get"><label class="sr" for="q-home">Buscar por assunto</label>
<input id="q-home" name="q" type="search" placeholder="Buscar um assunto…" autocomplete="off"><button type="submit">Buscar</button></form>
<div class="temas-linha">{"".join(f'<a class="chip t-{s}" href="tema/{s}/">{esc(n)}</a>' for n, (s, _, _) in visual.TEMAS.items())}</div></section>
{dia}
{noticias_sec}
{curios_sec}
{comece}
<section class="faixa in" id="temas" aria-labelledby="t-tem"><div class="titulo-bloco"><div><h2 id="t-tem">Explore por tema</h2><p>Escolha o assunto que desperta sua curiosidade.</p></div></div><div class="temas">{tiles_temas(arts, "")}</div></section>
<section class="faixa in" id="artigos" aria-labelledby="t-art"><div class="titulo-bloco"><div><h2 id="t-art">Todos os artigos</h2><p>Resposta rápida no começo, explicação completa e fontes no fim.</p></div></div>
{filtros}<div class="grade" id="todos">
{todos}
</div><p class="vazio" id="sem-resultado" hidden>Nenhum artigo com esses filtros ainda. Tire um filtro para ver mais.</p></section>
<section class="novidades"><div class="in"><div><h2>Receber novidades</h2><p>Sem pop-ups e sem cadastro: assine o feed RSS no seu leitor favorito e cada artigo novo aparece lá. Por enquanto não temos boletim por e-mail.</p></div>
<div class="caixa">Endereço do feed de artigos:<code>{esc(BASE)}feed.xml</code><br>Feed de notícias:<code>{esc(BASE)}noticias.xml</code></div></div></section>"""
    escreve("index.html", pagina(CFG["nome"], CFG["descricao"], corpo, "", "", ativo="inicio"))


def pagina_tema(nome, arts, noticias):
    s, desc, _ = visual.TEMAS[nome]
    meus = [a for a in arts if a["categoria"] == nome]
    minhas_not = [n for n in noticias if n["tema"] == nome][:6]
    cards = "".join(cartao(a, "../../") for a in meus) or '<p class="vazio">Ainda não há artigos neste tema. Eles chegam todo dia: volte em breve ou explore os outros temas abaixo.</p>'
    not_sec = ""
    if minhas_not:
        not_sec = (f'<section class="faixa" aria-labelledby="t-n"><div class="titulo-bloco"><h2 id="t-n">Notícias de {esc(nome.lower())}</h2><a class="mais" href="../../noticias/">Todas as notícias</a></div>'
                   f'<div class="grade">{"".join(cartao_noticia(n) for n in minhas_not)}</div><p class="nota-fonte">{NOTA_NOTICIAS}</p></section>')
    outros = "".join(
        f'<a class="chip t-{x}" href="../{x}/">{esc(n)}</a>' for n, (x, _, _) in visual.TEMAS.items() if n != nome)
    corpo = f"""<div class="in t-{s}"><div class="banner">{visual.cena(nome, uid())}</div>
<header class="cab-pag"><p class="kicker">Tema</p><h1>{esc(nome)}</h1><p class="lead">{esc(desc)}</p></header>
<section class="faixa" aria-label="Artigos"><div class="grade">{cards}</div></section>
{not_sec}
<section class="faixa" aria-label="Outros temas"><div class="titulo-bloco"><h2>Outros temas</h2></div><div class="temas-linha">{outros}</div></section></div>"""
    escreve(f"tema/{s}/index.html", pagina(nome, desc, corpo, "../../", f"tema/{s}/"))


def pagina_noticias(noticias):
    if noticias:
        cards = "".join(cartao_noticia(n) for n in noticias)
        bloco = f'<div class="grade">{cards}</div>'
    else:
        bloco = '<p class="vazio">As notícias aparecem aqui todo dia de manhã.</p>'
    corpo = f"""<div class="in"><header class="cab-pag"><p class="kicker">Notícias</p><h1>Notícias de ciência</h1>
<p class="lead">O que a ciência anunciou nos últimos dias, em resumos curtos, sempre com a data e a fonte originais.</p></header>
<section class="faixa" aria-label="Notícias">{bloco}<p class="nota-fonte">{NOTA_NOTICIAS} Para receber por RSS: <a href="../noticias.xml">noticias.xml</a>.</p></section></div>"""
    escreve("noticias/index.html", pagina("Notícias de ciência", "Notícias recentes de ciência, resumidas, com data e fonte à vista.",
                                          corpo, "../", "noticias/", ativo="noticias"))


def pagina_busca(arts):
    chips = "".join(f'<button type="button" class="chip t-{s}" data-tema="{s}" aria-pressed="false">{esc(n)}</button>' for n, (s, _, _) in visual.TEMAS.items())
    niveis = '<option value="">Todos</option>' + "".join(f'<option value="{k}">{v}</option>' for k, v in NIVEIS.items())
    sem_js = "".join(f'<li><a href="../artigos/{a["slug"]}/">{esc(a["titulo"])}</a></li>' for a in arts)
    corpo = f"""<section class="in" id="busca-app" aria-busy="true"><header class="cab-pag"><p class="kicker">Buscar</p><h1>O que você quer descobrir?</h1>
<p class="lead">Procure por assunto e filtre por tema ou nível de leitura. Busca artigos, curiosidades e notícias.</p></header>
<form class="busca" role="search" action="./" method="get"><label class="sr" for="q">Buscar por assunto</label>
<input id="q" name="q" type="search" placeholder="Ex.: ozônio, coração, buraco negro" autocomplete="off"><button type="submit">Buscar</button></form>
<div class="temas-linha" role="group" aria-label="Filtrar por tema">{chips}</div>
<div class="opcoes"><label>Nível de leitura<select id="nivel">{niveis}</select></label><span class="aviso-vivo" id="contagem" aria-live="polite"></span></div>
<div class="resultados" id="resultados"></div>
<noscript><p class="nota-fonte">A busca precisa de JavaScript. Sem ele, escolha um tema no menu ou abra um artigo da lista:</p><ul>{sem_js}</ul></noscript></section>"""
    escreve("buscar/index.html", pagina("Buscar", "Busque artigos, curiosidades e notícias de ciência por assunto, tema e nível.", corpo, "../", "buscar/", ativo="buscar"))


def pagina_salvos():
    corpo = """<section class="in" id="salvos-app"><header class="cab-pag"><p class="kicker">Salvos</p><h1>Seus artigos salvos</h1>
<p class="lead">A lista fica só neste navegador: não pedimos cadastro e não enviamos nada para lugar nenhum.</p></header>
<p class="vazio" id="salvos-msg">Carregando…</p><div class="resultados" id="salvos-lista"></div></section>"""
    escreve("salvos/index.html", pagina("Salvos", "Seus artigos salvos neste navegador.", corpo, "../", "salvos/", ativo="salvos", noindex=True))


def pagina_como():
    corpo = """<div class="in texto"><h1>Como fazemos</h1>
<p>O nome é uma promessa: aqui nada entra nos artigos sem ser <strong>conferido</strong>. O texto abaixo é o método que cada artigo precisa cumprir.</p>
<h2>As regras dos artigos</h2>
<ul>
<li><strong>Só fonte confiável.</strong> Revistas científicas, universidades, agências e institutos oficiais (como NASA, NOAA, USGS, OMS, Fiocruz, INPE) e livros-texto. Blog, rede social e site sem autor não valem como fonte.</li>
<li><strong>Link aberto antes de citar.</strong> Cada fonte é aberta e lida; a data da conferência fica ao lado dela, no fim do artigo.</li>
<li><strong>Fonte ao lado de cada número.</strong> Todo parágrafo com número, data ou medida carrega o <sup class="cit"><a href="#">[n]</a></sup> da fonte. O validador do site recusa o artigo que não cumprir.</li>
<li><strong>Pelo menos duas fontes</strong> de organizações diferentes por artigo.</li>
<li><strong>"O que ainda não se sabe".</strong> Todo artigo separa o que está estabelecido do que ainda se discute.</li>
<li><strong>Segundo passe separado.</strong> Quem escreve o rascunho não é quem publica: outra rodada reabre todas as fontes e só libera o artigo se cada afirmação aparecer lá.</li>
<li><strong>Se duas boas fontes discordam,</strong> o artigo diz isso em vez de escolher uma.</li>
<li><strong>Erro corrigido em público.</strong> Corrigimos e anotamos na página de <a href="../correcoes/">correções</a>, com a data.</li>
</ul>
<h2>Curiosidades</h2>
<p>As curiosidades da página inicial são frases tiradas, palavra por palavra, de artigos já conferidos, e levam o número da fonte. O site recusa uma curiosidade que não esteja no texto do artigo.</p>
<h2>Notícias</h2>
<p>As notícias são resumos curtos, escritos por nós, de reportagens de instituições e veículos de confiança (NASA, NOAA, agências de fomento, universidades, grandes jornais). Sempre mostramos a data original e a fonte, com o link. Elas <strong>não têm a conferência completa dos artigos</strong>: servem para você saber o que está acontecendo e ir à fonte. Só entram links de sites de uma lista aprovada, e o site recusa a notícia que não cumprir isso.</p>
<h2>Níveis de leitura</h2>
<ul><li><strong>Iniciante:</strong> para quem está começando, sem termos difíceis.</li><li><strong>Intermediário:</strong> para quem já conhece o básico e quer entender o porquê.</li><li><strong>Avançado:</strong> mais detalhes e termos técnicos.</li></ul>
<p>Dentro de cada artigo, a <strong>resposta rápida</strong> vem primeiro, o <strong>explicando melhor</strong> traz o raciocínio completo e, quando o assunto pede, a parte <strong>para ir mais fundo</strong> aprofunda os conceitos difíceis aos poucos.</p>
<h2>Quem escreve</h2>
<p>Os textos são escritos com ajuda de inteligência artificial e conferidos contra as fontes citadas. Dizemos isso de propósito: a confiança vem de você poder abrir a fonte e checar, não de acreditar em nós.</p>
<h2>Limites</h2>
<p>Ciência muda. A data de "conferido em" mostra quando cada artigo foi checado pela última vez. Este site informa, não substitui médico, professor ou especialista.</p></div>"""
    corpo = corpo.replace('<a href="#">[n]</a>', '<a href="../como-fazemos/">n</a>')
    escreve("como-fazemos/index.html",
            pagina("Como fazemos", "O método de pesquisa e conferência de cada artigo do Ciência Conferida.", corpo, "../",
                   "como-fazemos/", ativo="como"))


def pagina_correcoes():
    arq = RAIZ / "correcoes.json"
    itens = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else []
    if itens:
        lis = "".join(f"<li><strong>{data_curta(c['data'])}</strong>, {esc(c['artigo'])}: {esc(c['o_que_mudou'])}</li>"
                      for c in sorted(itens, key=lambda c: c["data"], reverse=True))
        corpo_c = f"<ul>{lis}</ul>"
    else:
        corpo_c = "<p>Nenhuma correção até agora. Quando houver, ela aparece aqui, com a data e o que mudou.</p>"
    corpo = f"""<div class="in texto"><h1>Correções</h1>
<p>Errar faz parte; esconder o erro não. Toda correção feita depois da publicação fica registrada aqui.</p>
{corpo_c}
<p>Achou algo errado? <a href="{esc(CFG['repo'])}/issues/new">Avise aqui</a>.</p></div>"""
    escreve("correcoes/index.html",
            pagina("Correções", "Registro público das correções feitas nos artigos.", corpo, "../", "correcoes/", ativo="corr"))


def pagina_sobre():
    a = CFG.get("analytics") or {}
    medida = ("Medimos as visitas com o GoatCounter, que não usa cookies e não guarda dados pessoais." if (a.get("tipo") or "").lower() == "goatcounter" and a.get("codigo")
              else "Medimos o número de visitas para saber quais assuntos interessam." if a.get("codigo") else "")
    corpo = f"""<div class="in texto"><h1>Sobre</h1>
<p>Ciência Conferida é um site independente de divulgação científica para quem é curioso, de criança a adulto. A ideia é simples: responder perguntas do dia a dia
com uma resposta curta, uma explicação completa e a fonte de cada fato ao alcance de um clique.</p>
<p>Os assuntos são variados (espaço, animais, corpo humano, tecnologia, meio ambiente e física) porque a curiosidade também é. O que não varia é o método descrito em <a href="../como-fazemos/">como fazemos</a>.</p>
<p>Não usamos pop-ups nem pedimos cadastro. Os artigos que você salva ficam só no seu navegador. Para receber novidades, use o <a href="../feed.xml">feed RSS</a>.</p>
<p>O código do site e todos os artigos são abertos: <a href="{esc(CFG['repo'])}">{esc(CFG['repo'])}</a>.</p>
<p>{medida}</p></div>"""
    escreve("sobre/index.html", pagina("Sobre", "O que é o Ciência Conferida e como o site funciona.", corpo, "../", "sobre/", ativo="sobre"))


def pagina_404():
    base = "/" + CFG["url"].split("//", 1)[1].split("/", 1)[1] if "/" in CFG["url"].split("//", 1)[1] else "/"
    corpo = f'<div class="in texto"><h1>Página não encontrada</h1><p>Esse endereço não existe (ainda). <a href="{base}">Volte para o início</a> ou <a href="{base}buscar/">busque um assunto</a>.</p></div>'
    escreve("404.html", pagina("Página não encontrada", "Página não encontrada.", corpo, base, "404.html", noindex=True))


def feeds_e_mapa(arts, noticias):
    def rfc(iso):
        return date.fromisoformat(iso).strftime("%a, %d %b %Y") + " 12:00:00 +0000"
    itens = "".join(
        f"<item><title>{esc(a['titulo'])}</title><link>{BASE}artigos/{a['slug']}/</link><guid>{BASE}artigos/{a['slug']}/</guid>"
        f"<pubDate>{rfc(a['publicado'])}</pubDate><description>{esc(a['resumo'])}</description></item>" for a in arts[:20])
    escreve("feed.xml", f'<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>{esc(CFG["nome"])}</title>'
            f'<link>{BASE}</link><description>{esc(CFG["descricao"])}</description><language>pt-BR</language>{itens}</channel></rss>')
    itens_n = "".join(
        f"<item><title>{esc(n['titulo'])} ({esc(n['fonte'])})</title><link>{esc(n['url'])}</link><guid>{esc(n['url'])}</guid>"
        f"<pubDate>{rfc(n['publicado'])}</pubDate><description>{esc(n['resumo'])} Resumo de reportagem de terceiros, sem a conferência completa dos artigos.</description></item>"
        for n in noticias[:30])
    escreve("noticias.xml", f'<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>{esc(CFG["nome"])}: notícias de ciência</title>'
            f'<link>{BASE}noticias/</link><description>Resumos curtos de notícias de ciência, com data e fonte.</description><language>pt-BR</language>{itens_n}</channel></rss>')
    urls = [(BASE, arts[0]["conferido"] if arts else "")] + [(f"{BASE}artigos/{a['slug']}/", a["conferido"]) for a in arts]
    urls += [(f"{BASE}tema/{s}/", "") for _, (s, _, _) in visual.TEMAS.items()]
    urls += [(f"{BASE}{p}/", "") for p in ("noticias", "buscar", "como-fazemos", "correcoes", "sobre")]
    corpo = "".join(f"<url><loc>{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>" for u, d in urls)
    escreve("sitemap.xml", f'<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{corpo}</urlset>')
    escreve("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")


def indice(arts, noticias):
    dados = {
        "artigos": [{"slug": a["slug"], "titulo": a["titulo"], "resumo": a["resumo"], "tema": a["categoria"],
                     "tema_slug": visual.slug_tema(a["categoria"]), "nivel": a["nivel"], "nivel_nome": NIVEIS[a["nivel"]],
                     "url": f"artigos/{a['slug']}/", "data": a["publicado"], "conf": a["conferido"], "min": minutos(a["corpo"]),
                     "curiosidades": [sem_marcas(c) for c in a["curiosidades"]]} for a in arts],
        "noticias": [{"titulo": n["titulo"], "resumo": n["resumo"], "fonte": n["fonte"], "url": n["url"], "data": n["publicado"],
                      "tema": n["tema"], "tema_slug": visual.slug_tema(n["tema"])} for n in noticias],
    }
    escreve("indice.json", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))


def main():
    if "--sem-validar" not in sys.argv:
        r = subprocess.run([sys.executable, str(RAIZ / "validar.py")])
        if r.returncode != 0:
            print("Validação falhou: o site NÃO foi gerado.")
            return 1
    arts = [ler_artigo(p) for p in sorted((RAIZ / "artigos").glob("*.md"))]
    arts.sort(key=lambda a: (a["publicado"], a["slug"]), reverse=True)
    noticias = ler_noticias()
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")
    escreve("estilo.css", CSS)
    escreve("app.js", JS)
    shutil.copytree(RAIZ / "assets" / "fontes", SAIDA / "fontes")
    for a in arts:
        pagina_artigo(a, arts)
    pagina_inicio(arts, noticias)
    for nome in visual.TEMAS:
        pagina_tema(nome, arts, noticias)
    pagina_noticias(noticias)
    pagina_busca(arts)
    pagina_salvos()
    pagina_como()
    pagina_correcoes()
    pagina_sobre()
    pagina_404()
    feeds_e_mapa(arts, noticias)
    indice(arts, noticias)
    print(f"site gerado em docs/: {len(arts)} artigo(s), {len(noticias)} notícia(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
