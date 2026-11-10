#!/usr/bin/env python3
"""Gera o site (pasta docs/) a partir de artigos/*.md e site.json. Só biblioteca padrão.

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

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
import visual  # noqa: E402
SAIDA = RAIZ / "docs"
CFG = json.loads((RAIZ / "site.json").read_text(encoding="utf-8"))
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]


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


def ler_artigo(caminho):
    """Lê um artigo .md: cabeçalho entre '---' e corpo em markdown simples."""
    texto = caminho.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)\Z", texto, re.S)
    if not m:
        raise ValueError(f"{caminho.name}: sem cabeçalho '---'")
    cab, corpo = m.groups()
    meta = {"fontes": [], "arquivo": caminho.name}
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
        else:
            meta[k] = v
    meta["corpo"] = corpo.strip()
    return meta


# ---------- markdown simples ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]\[]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\[(\d+)\]", r'<sup class="cit"><a href="#fonte-\1" aria-label="Fonte \1">[\1]</a></sup>', s)
    return s


def blocos(texto):
    """Converte um trecho de markdown (sem títulos ##) em HTML."""
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
            saida.append(f"<h3>{inline(t[4:])}</h3>")
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
    """Divide o corpo nas seções '## ' e devolve o HTML de cada uma, com classe própria."""
    partes = re.split(r"(?m)^## ", "\n" + meta["corpo"])
    secoes = []
    for p in partes[1:]:
        titulo, _, resto = p.partition("\n")
        titulo = titulo.strip()
        cls = "secao"
        if titulo.lower().startswith("resposta rápida"):
            cls = "secao resposta"
        elif titulo.lower().startswith("o que ainda"):
            cls = "secao ainda"
        secoes.append(f'<section class="{cls}" id="{slug_titulo(titulo)}"><h2>{inline(titulo)}</h2>\n{blocos(resto)}</section>')
    return "\n".join(secoes)


# ---------- modelo de página ----------
CSS = """
@font-face{font-family:"Fraunces";src:url(fontes/fraunces-600.woff2) format("woff2");font-weight:600;font-style:normal;font-display:swap}
:root{--bg:#fffaf1;--card:#ffffff;--tx:#1d2540;--mu:#59637c;--ln:#eadfc9;--ac:#0f766e;--acb:#d7f3ee;--hl:#f5a524;--hl2:#f7cf7a;--hlb:#fff3d1;--pu:#7c3aed;--pub:#f0e9ff;--lk:#1d4ed8;--on:#ffffff;
 --hero1:#ffeec4;--hero2:#ffd5cf;--foot:#1d2540;--foott:#d9e0f5;--sh:rgba(29,37,64,.32);
 --fh:"Fraunces","Iowan Old Style",Georgia,serif;--fu:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif}
@media(prefers-color-scheme:dark){:root{--bg:#0f1626;--card:#172038;--tx:#eaf0ff;--mu:#a9b6d6;--ln:#2b3857;--ac:#5eead4;--acb:#123a3c;--hl:#fbbf24;--hl2:#7a5a12;--hlb:#2e2710;--pu:#c4b5fd;--pub:#241f42;--lk:#93c5fd;--on:#06201d;
 --hero1:#26203f;--hero2:#38213a;--foot:#0a101d;--foott:#aab7d8;--sh:rgba(0,0,0,.6);color-scheme:dark}}
.c-terra{--cc:#2563eb;--cs:#e1eeff}.c-espaco{--cc:#5a49d6;--cs:#e8e5ff}.c-corpo{--cc:#d9365f;--cs:#ffe1e8}.c-vida{--cc:#17894f;--cs:#dcf5e6}
.c-materia{--cc:#c26a00;--cs:#ffeecf}.c-tec{--cc:#0c7c75;--cs:#d6f4f0}.c-mente{--cc:#7c3aed;--cs:#efe6ff}
@media(prefers-color-scheme:dark){.c-terra{--cc:#8dbbff;--cs:#16284a}.c-espaco{--cc:#b5acff;--cs:#201c4d}.c-corpo{--cc:#ff9db4;--cs:#44202c}.c-vida{--cc:#7fe0a8;--cs:#173a28}
.c-materia{--cc:#ffc15e;--cs:#43300f}.c-tec{--cc:#6ee7dc;--cs:#123a38}.c-mente{--cc:#c9b3ff;--cs:#2c2150}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
body{margin:0;background:var(--bg);color:var(--tx);font:400 1.125rem/1.75 var(--fu)}
a{color:var(--lk)}a:hover{text-decoration-thickness:2px}
:focus-visible{outline:3px solid var(--ac);outline-offset:3px;border-radius:6px}
.in{max-width:68rem;margin:0 auto;padding-left:max(18px,env(safe-area-inset-left,0px));padding-right:max(18px,env(safe-area-inset-right,0px))}
.art{max-width:46rem}
header.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--ln)}
header.top .in{display:flex;flex-wrap:wrap;gap:6px 22px;align-items:center;justify-content:space-between;padding-top:12px;padding-bottom:12px}
.logo{font:600 1.45rem/1.1 var(--fh);color:var(--tx);text-decoration:none;display:flex;align-items:center;gap:10px}
.logo .ck{display:inline-grid;place-items:center;width:36px;height:36px;border-radius:12px;background:var(--ac);color:var(--on);font:800 1.15rem var(--fu);transform:rotate(-6deg)}
nav.menu{display:flex;flex-wrap:wrap;gap:4px 8px;font:700 .95rem var(--fu)}
nav.menu a{color:var(--mu);text-decoration:none;padding:7px 13px;border-radius:99px}
nav.menu a:hover{background:var(--acb);color:var(--ac)}
nav.menu a[aria-current]{background:var(--tx);color:var(--bg)}
h1,h2,h3{font-family:var(--fh);font-weight:600;line-height:1.15;text-wrap:balance;margin:0}
h1{font-size:clamp(2.1rem,6.2vw,3.3rem);letter-spacing:-.015em;margin:.3em 0 .35em}
h2{font-size:clamp(1.55rem,4vw,2rem);margin:2em 0 .5em}
h3{font-size:1.3rem;margin:1.5em 0 .35em}
p{margin:.85em 0}
.chip{display:inline-block;font:800 .72rem/1 var(--fu);text-transform:uppercase;letter-spacing:.09em;color:var(--cc,var(--ac));background:var(--cs,var(--acb));padding:7px 13px;border-radius:99px}
.meta{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;font:600 .92rem var(--fu);color:var(--mu);margin:.4em 0 1.4em}
.selo{display:inline-flex;align-items:center;gap:7px;background:var(--acb);color:var(--ac);border-radius:99px;padding:4px 14px 4px 5px;font:800 .82rem var(--fu)}
.selo i{font-style:normal;display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--ac);color:var(--on);font-size:.8rem}
.banner{border-radius:26px;overflow:hidden;aspect-ratio:21/8;margin:20px 0 26px;box-shadow:0 18px 40px -24px var(--sh)}
.banner svg,.thumb svg{display:block;width:100%;height:100%}
.art p,.art li{max-width:42rem}
.secao>p:first-of-type{margin-top:.2em}
.resposta{background:var(--hlb);border:2px solid var(--hl2);border-radius:24px;padding:26px 28px 12px;margin:2.6em 0 1.8em}
.resposta h2{display:inline-block;margin:-46px 0 12px;background:var(--hl);color:#3a2400;font:800 .8rem/1 var(--fu);text-transform:uppercase;letter-spacing:.1em;padding:9px 16px;border-radius:99px}
.resposta p{font-size:1.28rem;line-height:1.6}
.ainda{background:var(--pub);border-radius:24px;padding:4px 28px 14px;margin:2.6em 0}
.ainda h2{display:flex;align-items:center;gap:12px;color:var(--pu);font-size:1.55rem}
.ainda h2::before{content:"?";flex:none;display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:var(--pu);color:#fff;font:800 1.2rem var(--fu)}
.cit{margin-left:2px;vertical-align:baseline}
.cit a{display:inline-block;background:var(--acb);color:var(--ac);border-radius:7px;padding:0 6px;font:800 .72rem/1.55 var(--fu);text-decoration:none;position:relative;top:-.45em}
.cit a:hover{background:var(--ac);color:var(--on)}
blockquote{margin:1.2em 0;padding:.6em 1.2em;border-left:6px solid var(--hl);background:var(--hlb);border-radius:0 16px 16px 0;color:var(--tx)}
ul,ol{padding-left:1.35em}li{margin:.45em 0}li::marker{color:var(--ac);font-weight:800}
.fontes{background:var(--card);border:2px solid var(--ln);border-radius:24px;padding:6px 28px 18px;margin:2.8em 0 1.6em;font-size:1rem}
.fontes h2{font-size:1.4rem;margin:.9em 0 .3em}
.fontes ol{padding-left:1.5em}.fontes li{margin:.7em 0;overflow-wrap:anywhere;line-height:1.55}
.fontes li:target{background:var(--hlb);border-radius:8px;box-shadow:0 0 0 6px var(--hlb)}
.erro{margin:1.6em 0 3em;padding:16px 20px;background:var(--acb);border-radius:18px;font:600 .96rem/1.55 var(--fu);color:var(--tx)}
.hero{background:linear-gradient(135deg,var(--hero1),var(--hero2));overflow:hidden}
.hero .in{display:grid;grid-template-columns:1.15fr .85fr;gap:20px 34px;align-items:center;padding-top:44px;padding-bottom:44px}
.kicker{font:800 .8rem/1.3 var(--fu);text-transform:uppercase;letter-spacing:.12em;color:var(--ac);margin:0 0 6px}
.hero h1{font-size:clamp(2.4rem,7vw,4.2rem);margin:.1em 0 .3em}
.lead{font-size:clamp(1.1rem,2.6vw,1.3rem);color:var(--mu);max-width:34rem;margin:0 0 1.4em}
.acoes{display:flex;flex-wrap:wrap;gap:12px}
.btn{display:inline-block;background:var(--ac);color:var(--on);font:800 1rem var(--fu);padding:14px 24px;border-radius:99px;text-decoration:none;box-shadow:0 12px 24px -14px var(--ac);transition:transform .15s}
.btn:hover{transform:translateY(-2px)}
.btn.sec{background:transparent;color:var(--tx);border:2px solid var(--tx);box-shadow:none}
.hero-art svg{width:100%;max-width:25rem;height:auto;display:block;margin:0 auto;filter:drop-shadow(0 20px 20px rgba(29,37,64,.18))}
.bloco{padding-top:8px;padding-bottom:12px}
.bloco>h2{margin:1.8em 0 .6em}
.passos{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,15rem),1fr));gap:18px}
.passo{background:var(--card);border:2px solid var(--ln);border-radius:22px;padding:22px;margin:0}
.passo h3{margin:.7em 0 .3em;font-size:1.25rem}.passo p{margin:0;color:var(--mu);font-size:1rem;line-height:1.55}
.num{display:grid;place-items:center;width:44px;height:44px;border-radius:14px;background:var(--cc);color:#fff;font:800 1.25rem var(--fu)}
.lista{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,19rem),1fr));gap:22px;margin:0 0 1em}
.card{display:flex;flex-direction:column;background:var(--card);border-radius:24px;overflow:hidden;text-decoration:none;color:var(--tx);border:2px solid var(--ln);transition:transform .2s,box-shadow .2s,border-color .2s}
.card:hover{transform:translateY(-5px);box-shadow:0 22px 40px -26px var(--sh);border-color:var(--cc)}
.thumb{aspect-ratio:2/1;overflow:hidden}
.cb{padding:18px 22px 22px;display:flex;flex-direction:column;align-items:flex-start;gap:11px;flex:1}
.card h3{margin:0;font-size:1.4rem}
.card p{margin:0;color:var(--mu);font-size:1rem;line-height:1.55;flex:1}
footer.pe{background:var(--foot);color:var(--foott);margin-top:3.5em}
footer.pe .in{padding-top:28px;padding-bottom:max(30px,env(safe-area-inset-bottom,0px));font:500 .93rem/1.7 var(--fu)}
footer.pe a{color:var(--foott)}footer.pe strong{font:600 1.2rem var(--fh);color:#fff}
@media(max-width:44rem){.hero .in{grid-template-columns:1fr;padding-top:28px;padding-bottom:30px}.hero-art{order:-1}.hero-art svg{max-width:13rem}
.banner{aspect-ratio:16/8;border-radius:20px}.resposta,.ainda,.fontes{padding-left:20px;padding-right:20px}nav.menu{font-size:.85rem;gap:0}nav.menu a{padding:6px 9px}.logo{font-size:1.3rem}}
@media print{header.top,footer.pe,.hero-art,.banner{display:none}body{background:#fff;color:#000}}
"""

CSS_V = hashlib.md5(CSS.encode("utf-8")).hexdigest()[:8]  # muda quando o visual muda: o navegador não usa CSS velho
JS_TEMA = ""  # tema segue o sistema; sem JavaScript


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


def pagina(titulo, desc, corpo, rel, url_rel, ativo="", og_tipo="website", jsonld=None, cru=False):
    nome = CFG["nome"]
    t = nome if titulo == nome else f"{titulo} · {nome}"
    canon = CFG["url"].rstrip("/") + "/" + url_rel
    home = rel or "./"
    menu = [("", "Início", "inicio"), ("como-fazemos/", "Como fazemos", "como"), ("correcoes/", "Correções", "corr"),
            ("sobre/", "Sobre", "sobre")]
    nav = "".join(f'<a href="{rel}{u}"{" aria-current=page" if k == ativo else ""}>{n}</a>' for u, n, k in menu)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    miolo = corpo if cru else f'<main class="in art">\n{corpo}\n</main>'
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
<meta name="color-scheme" content="light dark">
<link rel="alternate" type="application/rss+xml" title="{esc(nome)}" href="{rel}feed.xml">
<link rel="preload" href="{rel}fontes/fraunces-600.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{rel}estilo.css?v={CSS_V}">
{ld}
{analytics_html()}
</head>
<body>
<header class="top"><div class="in"><a class="logo" href="{home}"><span class="ck" aria-hidden="true">✓</span>{esc(nome)}</a><nav class="menu" aria-label="Principal">{nav}</nav></div></header>
{miolo}
<footer class="pe"><div class="in"><p><strong>{esc(nome)}</strong><br>{esc(CFG['slogan'])}. Os textos são escritos com ajuda de inteligência artificial e conferidos contra as fontes citadas em cada artigo
(<a href="{rel}como-fazemos/">como fazemos</a>). Viu algum erro? <a href="{esc(CFG['repo'])}/issues/new">Avise aqui</a> e a gente corrige e registra na página de <a href="{rel}correcoes/">correções</a>.</p></div></footer>
</body>
</html>
"""


def escreve(rel_path, conteudo):
    p = SAIDA / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(conteudo, encoding="utf-8")


# ---------- páginas ----------
def pagina_artigo(a):
    fontes = "".join(
        f'<li id="fonte-{i}"><a href="{esc(f["url"])}" rel="noopener">{esc(f["titulo"])}</a>, {esc(f["instituicao"])}. '
        f'Aberta e conferida em {data_curta(f["acessado"])}.</li>' for i, f in enumerate(a["fontes"], 1))
    sc = visual.slug_cat(a["categoria"])
    corpo = f"""<div class="c-{sc}">
<div class="banner">{visual.cena(a['categoria'], 'b')}</div>
<span class="chip">{esc(a['categoria'])}</span>
<h1>{esc(a['titulo'])}</h1>
<p class="meta"><span class="selo"><i aria-hidden="true">✓</i>Conferido em {data_br(a['conferido'])}</span><span>Publicado em {data_br(a['publicado'])}</span></p>
<article>
{corpo_html(a)}
<section class="fontes"><h2>Fontes</h2><ol>{fontes}</ol></section>
<p class="erro">Cada fato acima leva o número da fonte em que foi conferido. Se você achar algo errado ou desatualizado,
<a href="{esc(CFG['repo'])}/issues/new">avise aqui</a>: a gente corrige e anota na página de <a href="../../correcoes/">correções</a>.</p>
</article>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["titulo"], "inLanguage": "pt-BR",
          "datePublished": a["publicado"], "dateModified": a["conferido"], "description": a["resumo"],
          "publisher": {"@type": "Organization", "name": CFG["nome"]},
          "citation": [f["url"] for f in a["fontes"]]}
    escreve(f"artigos/{a['slug']}/index.html",
            pagina(a["titulo"], a["resumo"], corpo, "../../", f"artigos/{a['slug']}/", og_tipo="article", jsonld=ld))


def cartao(a, rel):
    sc = visual.slug_cat(a["categoria"])
    return (f'<a class="card c-{sc}" href="{rel}artigos/{a["slug"]}/"><div class="thumb">{visual.cena(a["categoria"], "c" + a["slug"][-6:])}</div>'
            f'<div class="cb"><span class="chip">{esc(a["categoria"])}</span><h3>{esc(a["titulo"])}</h3><p>{esc(a["resumo"])}</p>'
            f'<span class="selo"><i aria-hidden="true">✓</i>Conferido em {data_curta(a["conferido"])}</span></div></a>')


def pagina_inicio(arts):
    cards = "\n".join(cartao(a, "") for a in arts) or "<p>Os primeiros artigos chegam em breve.</p>"
    corpo = f"""<section class="hero"><div class="in">
<div><p class="kicker">Para curiosos de 8 a 80 anos</p><h1>{esc(CFG['slogan'])}</h1>
<p class="lead">{esc(CFG['descricao'])}</p>
<div class="acoes"><a class="btn" href="#artigos">Ver os artigos</a><a class="btn sec" href="como-fazemos/">Como conferimos</a></div></div>
<div class="hero-art">{visual.lupa()}</div></div></section>
<section class="in bloco"><h2>Como funciona</h2>
<ol class="passos">
<li class="passo c-terra"><span class="num">1</span><h3>Uma pergunta curiosa</h3><p>Escolhemos perguntas que crianças e adultos fazem de verdade: por que o céu é azul, por que o mar é salgado.</p></li>
<li class="passo c-vida"><span class="num">2</span><h3>Resposta rápida e explicação</h3><p>Primeiro a resposta em poucas linhas. Depois, o raciocínio completo, com os termos novos explicados.</p></li>
<li class="passo c-materia"><span class="num">3</span><h3>Fonte conferida em cada fato</h3><p>Todo número leva um <sup class="cit"><a href="como-fazemos/">n</a></sup> que aponta para a fonte aberta e conferida. E todo artigo diz o que a ciência ainda não sabe.</p></li>
</ol></section>
<section class="in bloco" id="artigos"><h2>Artigos</h2>
<div class="lista">
{cards}
</div></section>"""
    escreve("index.html", pagina(CFG["nome"], CFG["descricao"], corpo, "", "", ativo="inicio", cru=True))


def pagina_como():
    corpo = """<h1>Como fazemos</h1>
<p>O nome é uma promessa: aqui nada entra sem ser <strong>conferido</strong>. O texto abaixo é o método que cada artigo precisa cumprir.</p>
<h2>As regras</h2>
<ul>
<li><strong>Só fonte confiável.</strong> Revistas científicas, universidades, agências e institutos oficiais (como NASA, NOAA, USGS, OMS, Fiocruz, INPE) e livros-texto. Blog, rede social e site sem autor não valem como fonte.</li>
<li><strong>Link aberto antes de citar.</strong> Cada fonte é aberta e lida; a data da conferência fica ao lado dela, no fim do artigo.</li>
<li><strong>Fonte ao lado de cada número.</strong> Todo parágrafo com número, data ou medida carrega o <sup class="cit">[n]</sup> da fonte. O validador do site recusa o artigo que não cumprir.</li>
<li><strong>Pelo menos duas fontes</strong> de organizações diferentes por artigo.</li>
<li><strong>"O que ainda não se sabe".</strong> Todo artigo separa o que está estabelecido do que ainda se discute.</li>
<li><strong>Segundo passe separado.</strong> Quem escreve o rascunho não é quem publica: outra rodada reabre todas as fontes e só libera o artigo se cada afirmação aparecer lá.</li>
<li><strong>Se duas boas fontes discordam,</strong> o artigo diz isso em vez de escolher uma.</li>
<li><strong>Erro corrigido em público.</strong> Corrigimos e anotamos na página de <a href="../correcoes/">correções</a>, com a data.</li>
</ul>
<h2>Quem escreve</h2>
<p>Os textos são escritos com ajuda de inteligência artificial e conferidos contra as fontes citadas. Dizemos isso de propósito: a confiança vem de você poder abrir a fonte e checar, não de acreditar em nós.</p>
<h2>Dois jeitos de ler</h2>
<p>A <strong>resposta rápida</strong> cabe em poucas linhas e serve para quem tem pressa ou está começando. A parte <strong>explicando melhor</strong> traz o raciocínio completo, para quem quer ir fundo.</p>
<h2>Limites</h2>
<p>Ciência muda. A data de "conferido em" mostra quando cada artigo foi checado pela última vez. Este site informa, não substitui médico, professor ou especialista.</p>"""
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
    corpo = f"""<h1>Correções</h1>
<p>Errar faz parte; esconder o erro não. Toda correção feita depois da publicação fica registrada aqui.</p>
{corpo_c}
<p>Achou algo errado? <a href="{esc(CFG['repo'])}/issues/new">Avise aqui</a>.</p>"""
    escreve("correcoes/index.html",
            pagina("Correções", "Registro público das correções feitas nos artigos.", corpo, "../", "correcoes/", ativo="corr"))


def pagina_sobre():
    a = CFG.get("analytics") or {}
    medida = ("Medimos as visitas com o GoatCounter, que não usa cookies e não guarda dados pessoais." if (a.get("tipo") or "").lower() == "goatcounter" and a.get("codigo")
              else "Medimos o número de visitas para saber quais assuntos interessam." if a.get("codigo") else "")
    corpo = f"""<h1>Sobre</h1>
<p>Ciência Conferida é um site independente de divulgação científica para quem é curioso, de criança a adulto. A ideia é simples: responder perguntas do dia a dia
com uma resposta curta, uma explicação completa e a fonte de cada fato ao alcance de um clique.</p>
<p>Os assuntos são variados (céu, mar, corpo humano, espaço, bichos, tecnologia) porque a curiosidade também é. O que não varia é o método descrito em <a href="../como-fazemos/">como fazemos</a>.</p>
<p>O código do site e todos os artigos são abertos: <a href="{esc(CFG['repo'])}">{esc(CFG['repo'])}</a>.</p>
<p>{medida}</p>"""
    escreve("sobre/index.html", pagina("Sobre", "O que é o Ciência Conferida e como o site funciona.", corpo, "../", "sobre/", ativo="sobre"))


def pagina_404():
    corpo = '<h1>Página não encontrada</h1><p>Esse endereço não existe (ainda). <a href="./">Volte para o início</a>.</p>'
    # a 404 é servida em qualquer caminho: usa links absolutos a partir da base do site
    base = "/" + CFG["url"].split("//", 1)[1].split("/", 1)[1] if "/" in CFG["url"].split("//", 1)[1] else "/"
    corpo = corpo.replace('href="./"', f'href="{base}"')
    html_ = pagina("Página não encontrada", "Página não encontrada.", corpo, base, "404.html")
    escreve("404.html", html_)


def feed_e_mapa(arts):
    base = CFG["url"].rstrip("/") + "/"
    itens = "".join(
        f"<item><title>{esc(a['titulo'])}</title><link>{base}artigos/{a['slug']}/</link><guid>{base}artigos/{a['slug']}/</guid>"
        f"<pubDate>{date.fromisoformat(a['publicado']).strftime('%a, %d %b %Y')} 12:00:00 +0000</pubDate>"
        f"<description>{esc(a['resumo'])}</description></item>" for a in arts[:20])
    escreve("feed.xml", f'<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>{esc(CFG["nome"])}</title>'
            f'<link>{base}</link><description>{esc(CFG["descricao"])}</description><language>pt-BR</language>{itens}</channel></rss>')
    urls = [(base, arts[0]["conferido"] if arts else "")] + [(f"{base}artigos/{a['slug']}/", a["conferido"]) for a in arts]
    urls += [(f"{base}{p}/", "") for p in ("como-fazemos", "correcoes", "sobre")]
    corpo = "".join(f"<url><loc>{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>" for u, d in urls)
    escreve("sitemap.xml", f'<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{corpo}</urlset>')
    escreve("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n")


def main():
    if "--sem-validar" not in sys.argv:
        r = subprocess.run([sys.executable, str(RAIZ / "validar.py")])
        if r.returncode != 0:
            print("Validação falhou: o site NÃO foi gerado.")
            return 1
    arts = [ler_artigo(p) for p in sorted((RAIZ / "artigos").glob("*.md"))]
    arts.sort(key=lambda a: (a["publicado"], a["slug"]), reverse=True)
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")
    escreve("estilo.css", CSS.strip() + "\n")
    shutil.copytree(RAIZ / "assets" / "fontes", SAIDA / "fontes")
    for a in arts:
        pagina_artigo(a)
    pagina_inicio(arts)
    pagina_como()
    pagina_correcoes()
    pagina_sobre()
    pagina_404()
    feed_e_mapa(arts)
    print(f"site gerado em docs/: {len(arts)} artigo(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
