"""Ilustrações do site (SVG desenhado à mão em código, sem imagens externas) e cores por categoria.

Cada categoria tem uma cena (400x220) usada nos cartões e no topo dos artigos. `cena(cat, uid)` devolve o SVG;
`uid` evita ids repetidos quando a mesma cena aparece mais de uma vez na página.
"""
import math

# slug da classe CSS, cor principal, cor suave, texto da descrição (acessibilidade)
CATS = {
    "Terra e céu": ("terra", "um céu azul com sol, nuvens e colinas verdes"),
    "Espaço": ("espaco", "o espaço com estrelas, um planeta com anel e a Lua"),
    "Corpo humano": ("corpo", "um coração com a linha dos batimentos"),
    "Vida": ("vida", "uma planta brotando com folhas verdes"),
    "Matéria e energia": ("materia", "um átomo com órbitas e um raio"),
    "Tecnologia": ("tec", "um chip com trilhas de circuito e sinal sem fio"),
    "Mente e comportamento": ("mente", "uma lâmpada acesa e balões de pensamento"),
}


def slug_cat(cat):
    return CATS.get(cat, ("terra", ""))[0]


def _svg(corpo, desc, extra=""):
    return (f'<svg viewBox="0 0 400 220" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Ilustração: {desc}" '
            f'xmlns="http://www.w3.org/2000/svg"{extra}>{corpo}</svg>')


def _grad(uid, a, b, vertical=True):
    x2, y2 = ("0", "1") if vertical else ("1", "0")
    return (f'<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="{a}"/>'
            f'<stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="400" height="220" fill="url(#g{uid})"/>')


def _terra(uid):
    raios = "".join(
        f'<line x1="{310 + 40 * math.cos(a * math.pi / 4):.1f}" y1="{96 + 40 * math.sin(a * math.pi / 4):.1f}" '
        f'x2="{310 + 54 * math.cos(a * math.pi / 4):.1f}" y2="{96 + 54 * math.sin(a * math.pi / 4):.1f}"/>' for a in range(8))
    nuvem = lambda x, y, s: (f'<g transform="translate({x} {y}) scale({s})" fill="#fff"><ellipse cx="0" cy="0" rx="34" ry="16"/>'
                             f'<ellipse cx="-20" cy="-9" rx="20" ry="14"/><ellipse cx="14" cy="-14" rx="24" ry="17"/></g>')
    return (_grad(uid, "#3b95ff", "#d4ecff") + f'<circle cx="310" cy="96" r="30" fill="#ffd23f"/>'
            f'<g stroke="#ffd23f" stroke-width="6" stroke-linecap="round">{raios}</g>'
            + nuvem(92, 88, 1.1) + nuvem(214, 126, .8) + nuvem(356, 160, .55)
            + '<path d="M0 176 Q95 120 190 164 T400 146 V220 H0Z" fill="#4cc38a"/>'
              '<path d="M0 204 Q120 160 245 192 T400 186 V220 H0Z" fill="#2a9d6a"/>'
              '<rect x="78" y="168" width="6" height="22" rx="2" fill="#7a4b2a"/><circle cx="81" cy="160" r="16" fill="#1f7f55"/>')


def _espaco(uid):
    estrelas = [(30, 30, 2), (70, 80, 1.5), (120, 28, 2.4), (160, 70, 1.5), (210, 24, 2), (250, 60, 1.6), (360, 28, 2.4),
                (380, 90, 1.5), (40, 140, 1.8), (110, 190, 2), (190, 200, 1.5), (300, 196, 2), (345, 160, 1.6), (150, 120, 1.4)]
    st = "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in estrelas)
    return (_grad(uid, "#2a1f7a", "#0a0a2c") + f'<g fill="#fff" opacity=".9">{st}</g>'
            '<g transform="rotate(-18 280 110)"><ellipse cx="280" cy="110" rx="78" ry="16" fill="none" stroke="#ffe2b0" stroke-width="7" opacity=".55"/></g>'
            '<circle cx="280" cy="110" r="44" fill="#f5a35c"/><path d="M240 100 Q280 82 320 100 M238 120 Q280 104 322 122" stroke="#e4803a" stroke-width="6" fill="none" stroke-linecap="round" opacity=".7"/>'
            '<g transform="rotate(-18 280 110)"><path d="M202 110 A78 16 0 0 0 358 110" fill="none" stroke="#ffe2b0" stroke-width="7"/></g>'
            f'<circle cx="86" cy="150" r="22" fill="#8fd3ff"/><circle cx="78" cy="144" r="6" fill="#bfe6ff"/>'
            '<path d="M120 52 a26 26 0 1 0 22 40 a20 20 0 1 1 -22 -40z" fill="#fff3c4"/>')


def _corpo(uid):
    return (_grad(uid, "#ff9a8b", "#ff5c8a") +
            '<g fill="#fff" opacity=".16"><circle cx="60" cy="50" r="30"/><circle cx="350" cy="170" r="42"/><circle cx="330" cy="40" r="16"/><circle cx="40" cy="180" r="18"/></g>'
            '<path d="M200 168 C120 112 150 56 200 92 C250 56 280 112 200 168Z" fill="#fff"/>'
            '<path d="M200 168 C120 112 150 56 200 92 C250 56 280 112 200 168Z" fill="#ff4d6d" transform="translate(200 112) scale(.86) translate(-200 -112)"/>'
            '<polyline points="0,176 96,176 128,176 148,136 172,206 196,150 214,176 400,176" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')


def _vida(uid):
    return (_grad(uid, "#d3f7c9", "#79d99b") + '<circle cx="60" cy="48" r="26" fill="#ffe27a"/>'
            '<path d="M0 190 Q100 160 200 184 T400 176 V220 H0Z" fill="#8b5a33"/><path d="M0 206 Q130 186 250 204 T400 198 V220 H0Z" fill="#6f4426"/>'
            '<path d="M200 188 C198 150 204 120 200 84" stroke="#1f7a48" stroke-width="8" fill="none" stroke-linecap="round"/>'
            '<path d="M200 128 C150 130 128 96 132 70 C176 70 204 94 200 128Z" fill="#2fb36a"/>'
            '<path d="M200 106 C246 108 272 72 266 46 C224 48 198 72 200 106Z" fill="#43c97f"/>'
            '<path d="M200 140 C230 140 252 124 256 104 C230 102 204 114 200 140Z" fill="#259c5a"/>'
            '<g fill="#fff"><circle cx="318" cy="150" r="7"/><circle cx="332" cy="140" r="7"/><circle cx="332" cy="158" r="7"/><circle cx="306" cy="140" r="7"/><circle cx="306" cy="158" r="7"/></g><circle cx="319" cy="149" r="6" fill="#ffc83d"/>'
            '<rect x="318" y="156" width="3" height="32" fill="#1f7a48"/>')


def _materia(uid):
    orbitas = "".join(f'<ellipse cx="200" cy="112" rx="86" ry="28" transform="rotate({r} 200 112)"/>' for r in (0, 60, 120))
    return (_grad(uid, "#ffe08a", "#ff9f43") + f'<g fill="none" stroke="#fff" stroke-width="5" opacity=".95">{orbitas}</g>'
            '<circle cx="200" cy="112" r="17" fill="#e8590c"/><circle cx="196" cy="108" r="5" fill="#ffa94d"/>'
            '<g fill="#7a3e00"><circle cx="286" cy="112" r="8"/><circle cx="157" cy="37" r="8" transform="translate(0 0)"/><circle cx="157" cy="187" r="8"/></g>'
            '<polygon points="338,34 310,86 332,86 322,128 360,70 338,70" fill="#fff" opacity=".95"/>'
            '<g fill="#fff" opacity=".5"><circle cx="50" cy="48" r="10"/><circle cx="76" cy="170" r="16"/></g>')


def _tec(uid):
    tr = ('<g stroke="#5eead4" stroke-width="4" fill="none" stroke-linecap="round">'
          '<path d="M155 96 H90 V54 H40"/><path d="M155 124 H70 V170 H30"/><path d="M245 96 H310 V150 H370"/>'
          '<path d="M245 126 H340 V190"/><path d="M185 65 V30"/><path d="M215 65 V30 H260"/><path d="M200 155 V200"/></g>'
          '<g fill="#134e4a" stroke="#5eead4" stroke-width="4"><circle cx="40" cy="54" r="6"/><circle cx="30" cy="170" r="6"/>'
          '<circle cx="370" cy="150" r="6"/><circle cx="340" cy="190" r="6"/><circle cx="260" cy="30" r="6"/><circle cx="185" cy="30" r="6"/><circle cx="200" cy="200" r="6"/></g>')
    return (_grad(uid, "#0f766e", "#0b3b3a") + tr +
            '<rect x="155" y="65" width="90" height="90" rx="14" fill="#99f6e4"/><rect x="172" y="82" width="56" height="56" rx="8" fill="#0f766e"/>'
            '<path d="M186 110 h28 M200 96 v28" stroke="#99f6e4" stroke-width="5" stroke-linecap="round"/>'
            '<g fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".85"><path d="M312 52 a22 22 0 0 1 30 0"/><path d="M304 42 a34 34 0 0 1 46 0"/></g><circle cx="327" cy="62" r="4" fill="#fff"/>')


def _mente(uid):
    raios = "".join(
        f'<line x1="{200 + 54 * math.cos(a * math.pi / 5 - math.pi):.1f}" y1="{96 + 54 * math.sin(a * math.pi / 5 - math.pi):.1f}" '
        f'x2="{200 + 70 * math.cos(a * math.pi / 5 - math.pi):.1f}" y2="{96 + 70 * math.sin(a * math.pi / 5 - math.pi):.1f}"/>' for a in range(6))
    return (_grad(uid, "#cdbbff", "#7c4dff") + f'<g stroke="#fff3b0" stroke-width="6" stroke-linecap="round">{raios}</g>'
            '<circle cx="200" cy="100" r="42" fill="#ffe680"/><path d="M182 128 h36 v22 a12 12 0 0 1 -12 12 h-12 a12 12 0 0 1 -12 -12z" fill="#e5e7ff"/>'
            '<path d="M186 96 q14 -22 28 0 q-14 14 -28 0" fill="none" stroke="#e08a00" stroke-width="5" stroke-linecap="round"/>'
            '<g fill="#fff" opacity=".9"><circle cx="82" cy="150" r="12"/><circle cx="56" cy="176" r="8"/><circle cx="38" cy="194" r="5"/>'
            '<ellipse cx="320" cy="62" rx="34" ry="22"/><circle cx="296" cy="92" r="8"/><circle cx="282" cy="106" r="5"/></g>'
            '<text x="320" y="70" text-anchor="middle" font-size="22" font-weight="700" fill="#7c4dff" font-family="sans-serif">?</text>')


_CENAS = {"terra": _terra, "espaco": _espaco, "corpo": _corpo, "vida": _vida, "materia": _materia, "tec": _tec, "mente": _mente}


def cena(cat, uid):
    slug, desc = CATS.get(cat, ("terra", "um céu azul com sol, nuvens e colinas verdes"))
    return _svg(_CENAS[slug](uid), desc)


def lupa():
    """Ilustração da página inicial: lupa com a Terra dentro e um selo de conferido."""
    return ('<svg viewBox="0 0 340 300" role="img" aria-label="Ilustração: uma lupa mostrando o planeta Terra, com um selo verde de conferido" '
            'xmlns="http://www.w3.org/2000/svg">'
            '<defs><radialGradient id="lg" cx=".35" cy=".3" r=".9"><stop offset="0" stop-color="#7cc4ff"/><stop offset="1" stop-color="#2f6fe0"/></radialGradient>'
            '<clipPath id="lc"><circle cx="144" cy="134" r="78"/></clipPath></defs>'
            '<g fill="#fff" opacity=".9"><circle cx="40" cy="40" r="4"/><circle cx="300" cy="150" r="3"/><circle cx="26" cy="220" r="3"/><circle cx="310" cy="250" r="4"/></g>'
            '<path d="M204 192 L286 270" stroke="#e8851c" stroke-width="26" stroke-linecap="round"/><path d="M204 192 L286 270" stroke="#ffb454" stroke-width="10" stroke-linecap="round"/>'
            '<circle cx="144" cy="134" r="78" fill="url(#lg)"/>'
            '<g clip-path="url(#lc)" fill="#46c28a"><path d="M86 92 q26 -26 56 -8 q14 22 -4 34 q-30 6 -42 28 q-16 -14 -10 -54z"/>'
            '<path d="M168 138 q34 -14 52 12 q-4 40 -34 52 q-26 -10 -18 -64z"/><path d="M96 190 q20 -10 40 4 q-8 22 -30 24z"/></g>'
            '<g clip-path="url(#lc)" fill="#fff" opacity=".7"><ellipse cx="190" cy="92" rx="30" ry="9"/><ellipse cx="108" cy="170" rx="22" ry="7"/></g>'
            '<circle cx="144" cy="134" r="78" fill="none" stroke="#1d2a5e" stroke-width="14"/>'
            '<path d="M104 80 a64 64 0 0 1 36 -20" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round" opacity=".7"/>'
            '<circle cx="250" cy="70" r="36" fill="#22c55e" stroke="#fff" stroke-width="6"/>'
            '<path d="M232 71 l14 15 l26 -30" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg>')
