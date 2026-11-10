#!/usr/bin/env python3
"""Gera o site (pasta docs/) a partir de artigos/*.md e site.json. Só biblioteca padrão.

Uso:  python3 build.py            (valida e gera)
      python3 build.py --sem-validar
"""
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
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
:root{--bg:#fbf7ef;--card:#ffffff;--tx:#1c2430;--mu:#566170;--ln:#e4dccb;--ac:#0b6e6e;--acb:#d8f0ec;--hl:#e0a800;--hlb:#fff3c4;--lk:#0a5f9e;--on:#ffffff;
 --fh:"Trebuchet MS","Segoe UI",system-ui,-apple-system,sans-serif;--fb:Georgia,"Iowan Old Style","Palatino Linotype",Palatino,serif}
@media(prefers-color-scheme:dark){:root{--bg:#101a1c;--card:#172427;--tx:#e9f0ef;--mu:#a2b4b3;--ln:#2a3b3e;--ac:#5fd0c2;--acb:#173c38;--hl:#f6c945;--hlb:#3b3210;--lk:#8ccbf5;--on:#0d1311;color-scheme:dark}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--tx);font:400 1.125rem/1.7 var(--fb);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
a{color:var(--lk)}a:hover{text-decoration-thickness:2px}
:focus-visible{outline:3px solid var(--ac);outline-offset:2px}
.w{max-width:46rem;margin:0 auto}
header.top{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;justify-content:space-between;padding:18px 0 14px;border-bottom:2px solid var(--ln)}
.logo{font:800 1.35rem/1.1 var(--fh);color:var(--tx);text-decoration:none;display:flex;align-items:center;gap:10px}
.logo .ck{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--ac);color:var(--on);font-size:1.15rem}
nav.menu{display:flex;gap:16px;font:600 .95rem var(--fh)}
nav.menu a{color:var(--mu);text-decoration:none;padding:4px 2px;border-bottom:3px solid transparent}
nav.menu a:hover,nav.menu a[aria-current]{color:var(--tx);border-bottom-color:var(--hl)}
h1,h2,h3{font-family:var(--fh);line-height:1.2;text-wrap:balance}
h1{font-size:clamp(1.8rem,5vw,2.5rem);margin:.4em 0 .3em;letter-spacing:-.01em}
h2{font-size:1.45rem;margin:1.6em 0 .4em}
h3{font-size:1.15rem;margin:1.3em 0 .3em}
p{margin:.8em 0}
.slog{font:600 1.1rem var(--fh);color:var(--mu);margin:.2em 0 1.2em}
.cat{display:inline-block;font:700 .75rem var(--fh);text-transform:uppercase;letter-spacing:.09em;color:var(--ac);margin:1.2em 0 0}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;font:500 .9rem var(--fh);color:var(--mu);margin:.2em 0 1em}
.selo{font-family:var(--fh);display:inline-flex;align-items:center;gap:6px;background:var(--acb);color:var(--ac);border-radius:99px;padding:3px 12px 3px 6px;font-weight:700}
.selo i{font-style:normal;display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--ac);color:var(--on);font-size:.8rem}
.resposta{background:var(--hlb);border-left:8px solid var(--hl);border-radius:10px;padding:6px 20px 10px;margin:1.2em 0}
.resposta h2{margin:.6em 0 .2em;font-size:1.1rem;text-transform:uppercase;letter-spacing:.07em}
.resposta p{font-size:1.2rem}
.ainda{border-top:2px dashed var(--ln);margin-top:2em}
.cit{font:600 .72rem var(--fh);margin-left:1px}.cit a{text-decoration:none}
blockquote{margin:1em 0;padding:.2em 1em;border-left:5px solid var(--ln);color:var(--mu)}
.fontes{margin-top:2.2em;padding-top:.4em;border-top:2px solid var(--ln);font-size:1rem}
.fontes ol{padding-left:1.4em}.fontes li{margin:.6em 0;overflow-wrap:anywhere}
.fontes li:target{background:var(--hlb);border-radius:6px}
.erro{margin:2em 0;padding:14px 18px;background:var(--card);border:2px solid var(--ln);border-radius:12px;font:500 .95rem/1.5 var(--fh)}
.lista{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,16rem),1fr));gap:14px;margin:1.2em 0}
.card{background:var(--card);border:2px solid var(--ln);border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:6px;text-decoration:none;color:var(--tx)}
.card:hover{border-color:var(--ac)}
.card h3{margin:.1em 0;font-size:1.2rem}.card p{margin:0;font-size:.98rem;color:var(--mu);line-height:1.5}
.card .selo{align-self:flex-start;font-size:.78rem}
footer.pe{margin:3em 0 2em;padding-top:1em;border-top:2px solid var(--ln);font:500 .9rem/1.6 var(--fh);color:var(--mu)}
footer.pe a{color:var(--mu)}
@media print{header.top,footer.pe{display:none}body{background:#fff;color:#000}}
"""

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


def pagina(titulo, desc, corpo, rel, url_rel, ativo="", og_tipo="website", jsonld=None):
    nome = CFG["nome"]
    t = nome if titulo == nome else f"{titulo} · {nome}"
    canon = CFG["url"].rstrip("/") + "/" + url_rel
    home = rel or "./"
    menu = [("", "Início", "inicio"), ("como-fazemos/", "Como fazemos", "como"), ("correcoes/", "Correções", "corr"),
            ("sobre/", "Sobre", "sobre")]
    nav = "".join(f'<a href="{rel}{u}"{" aria-current=page" if k == ativo else ""}>{n}</a>' for u, n, k in menu)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
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
<link rel="stylesheet" href="{rel}estilo.css">
{ld}
{analytics_html()}
</head>
<body>
<div class="w">
<header class="top"><a class="logo" href="{home}"><span class="ck" aria-hidden="true">✓</span>{esc(nome)}</a><nav class="menu" aria-label="Principal">{nav}</nav></header>
<main>
{corpo}
</main>
<footer class="pe">{esc(nome)}: {esc(CFG['slogan'].lower())}. Os textos são escritos com ajuda de inteligência artificial e conferidos contra as fontes citadas em cada artigo
(<a href="{rel}como-fazemos/">como fazemos</a>). Viu algum erro? <a href="{esc(CFG['repo'])}/issues/new">Avise aqui</a> e a gente corrige e registra na página de <a href="{rel}correcoes/">correções</a>.</footer>
</div>
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
    corpo = f"""<article>
<span class="cat">{esc(a['categoria'])}</span>
<h1>{esc(a['titulo'])}</h1>
<p class="meta"><span class="selo"><i aria-hidden="true">✓</i>Conferido em {data_br(a['conferido'])}</span><span>Publicado em {data_br(a['publicado'])}</span></p>
{corpo_html(a)}
<section class="fontes"><h2>Fontes</h2><ol>{fontes}</ol></section>
<p class="erro">Cada fato acima leva o número da fonte em que foi conferido. Se você achar algo errado ou desatualizado,
<a href="{esc(CFG['repo'])}/issues/new">avise aqui</a>: a gente corrige e anota na página de <a href="../../correcoes/">correções</a>.</p>
</article>"""
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["titulo"], "inLanguage": "pt-BR",
          "datePublished": a["publicado"], "dateModified": a["conferido"], "description": a["resumo"],
          "publisher": {"@type": "Organization", "name": CFG["nome"]},
          "citation": [f["url"] for f in a["fontes"]]}
    escreve(f"artigos/{a['slug']}/index.html",
            pagina(a["titulo"], a["resumo"], corpo, "../../", f"artigos/{a['slug']}/", og_tipo="article", jsonld=ld))


def cartao(a, rel):
    return (f'<a class="card" href="{rel}artigos/{a["slug"]}/"><span class="cat" style="margin:0">{esc(a["categoria"])}</span>'
            f'<h3>{esc(a["titulo"])}</h3><p>{esc(a["resumo"])}</p>'
            f'<span class="selo"><i aria-hidden="true">✓</i>Conferido em {data_curta(a["conferido"])}</span></a>')


def pagina_inicio(arts):
    cards = "\n".join(cartao(a, "") for a in arts) or "<p>Os primeiros artigos chegam em breve.</p>"
    corpo = f"""<h1>{esc(CFG['slogan'])}</h1>
<p class="slog">{esc(CFG['descricao'])}</p>
<div class="resposta"><h2>Como funciona</h2><p>Cada artigo começa com uma <strong>resposta rápida</strong> e depois explica melhor. Todo número ou fato leva uma
<sup class="cit"><a href="como-fazemos/">[n]</a></sup> que aponta para a fonte onde ele foi conferido, e todo artigo diz <strong>o que a ciência ainda não sabe</strong>.</p></div>
<h2>Artigos</h2>
<div class="lista">
{cards}
</div>"""
    escreve("index.html", pagina(CFG["nome"], CFG["descricao"], corpo, "", "", ativo="inicio"))


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
