"""Ilustrações do site (SVG desenhado em código, sem imagens externas) e lista de temas.

Cada tema tem uma cena (400x220) usada nos cartões e no topo dos artigos, num estilo escuro (azul-marinho
com brilho). `cena(tema, uid)` devolve o SVG; `uid` evita ids repetidos quando a mesma cena aparece mais
de uma vez na página.
"""
import math

# nome -> (slug usado na URL e na classe CSS, descrição curta do tema, descrição da imagem para leitores de tela)
TEMAS = {
    "Espaço": ("espaco", "Planetas, estrelas, buracos negros e tudo o que existe além da Terra.",
               "o espaço com estrelas, um planeta com anel e a Lua"),
    "Animais": ("animais", "Como os bichos vivem, se orientam, se alimentam e se adaptam.",
                "uma coruja num galho, diante de uma lua grande"),
    "Corpo humano": ("corpo", "Como o coração, os pulmões, o cérebro e o resto do corpo funcionam.",
                     "um coração com a linha dos batimentos"),
    "Tecnologia": ("tecnologia", "Como funcionam as máquinas, a internet e as invenções do dia a dia.",
                   "um chip com trilhas de circuito e sinal sem fio"),
    "Meio ambiente": ("ambiente", "Mares, rios, clima, florestas e os processos que mantêm a Terra viva.",
                      "montanhas e um rio sob um céu noturno, com o Sol baixo"),
    "Física": ("fisica", "Luz, som, energia, matéria e as regras que movem o mundo.",
               "um átomo com órbitas de elétrons e uma onda"),
}
ORDEM = list(TEMAS)


def slug_tema(nome):
    return TEMAS.get(nome, ("espaco", "", ""))[0]


def nome_por_slug(slug):
    for n, (s, _, _) in TEMAS.items():
        if s == slug:
            return n
    return None


def _svg(corpo, desc, extra=""):
    return (f'<svg viewBox="0 0 400 220" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Ilustração: {desc}" '
            f'xmlns="http://www.w3.org/2000/svg"{extra}>{corpo}</svg>')


def _fundo(uid, a, b, brilho=None):
    """Fundo em degradê vertical; `brilho` = (cx, cy, raio, cor) adiciona um clarão suave."""
    s = (f'<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/>'
         f'<stop offset="1" stop-color="{b}"/></linearGradient>')
    extra = ""
    if brilho:
        cx, cy, r, cor = brilho
        s += (f'<radialGradient id="r{uid}" cx="{cx}" cy="{cy}" r="{r}" gradientUnits="userSpaceOnUse">'
              f'<stop offset="0" stop-color="{cor}" stop-opacity=".55"/><stop offset="1" stop-color="{cor}" stop-opacity="0"/></radialGradient>')
        extra = f'<rect width="400" height="220" fill="url(#r{uid})"/>'
    return s + f'</defs><rect width="400" height="220" fill="url(#g{uid})"/>' + extra


def _estrelas(pts, cor="#fff", op=".85"):
    return f'<g fill="{cor}" opacity="{op}">' + "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in pts) + "</g>"


E1 = [(30, 30, 1.6), (70, 80, 1.2), (120, 28, 2), (160, 70, 1.2), (210, 24, 1.6), (250, 60, 1.3), (360, 28, 2),
      (380, 90, 1.2), (40, 140, 1.5), (110, 190, 1.6), (190, 200, 1.2), (300, 196, 1.6), (345, 160, 1.3), (150, 120, 1.1)]


def _espaco(uid):
    return (_fundo(uid, "#1b1660", "#050b24", (280, 110, 190, "#6d5bff")) + _estrelas(E1)
            + f'<defs><linearGradient id="p{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffb08a"/><stop offset="1" stop-color="#d9467a"/></linearGradient></defs>'
              '<g transform="rotate(-18 280 110)"><ellipse cx="280" cy="110" rx="80" ry="16" fill="none" stroke="#c4b5fd" stroke-width="6" opacity=".55"/></g>'
              f'<circle cx="280" cy="110" r="44" fill="url(#p{uid})"/>'
              '<path d="M240 100 Q280 82 320 100 M238 120 Q280 104 322 122" stroke="#9d2a63" stroke-width="5" fill="none" stroke-linecap="round" opacity=".5"/>'
              '<g transform="rotate(-18 280 110)"><path d="M200 110 A80 16 0 0 0 360 110" fill="none" stroke="#c4b5fd" stroke-width="6"/></g>'
              '<circle cx="86" cy="150" r="20" fill="#22d3ee" opacity=".9"/><circle cx="79" cy="144" r="6" fill="#a5f3fc"/>'
              '<path d="M120 52 a26 26 0 1 0 22 40 a20 20 0 1 1 -22 -40z" fill="#fef3c7"/>')


def _animais(uid):
    return (_fundo(uid, "#0c2f45", "#06192c", (300, 70, 170, "#38bdf8")) + _estrelas(E1[:9], "#e0f2fe", ".7")
            + '<circle cx="306" cy="72" r="38" fill="#e0f2fe"/><circle cx="294" cy="62" r="7" fill="#bae6fd"/><circle cx="318" cy="86" r="5" fill="#bae6fd"/>'
              '<path d="M0 168 Q120 150 230 166 T400 156 V220 H0Z" fill="#082a3a"/>'
              '<path d="M-10 150 Q110 138 210 148 T410 140" stroke="#7c5a3a" stroke-width="11" fill="none" stroke-linecap="round"/>'
              '<path d="M60 146 l-22 -22 M92 144 l8 -26" stroke="#7c5a3a" stroke-width="5" stroke-linecap="round"/>'
              '<g transform="translate(150 98)"><ellipse cx="0" cy="26" rx="34" ry="42" fill="#5b6f8f"/><ellipse cx="0" cy="38" rx="21" ry="28" fill="#d7e3f7"/>'
              '<path d="M-28 -6 L-34 -30 L-12 -14Z M28 -6 L34 -30 L12 -14Z" fill="#5b6f8f"/>'
              '<circle cx="0" cy="-2" r="30" fill="#6f84a6"/><circle cx="-13" cy="-4" r="13" fill="#fef3c7"/><circle cx="13" cy="-4" r="13" fill="#fef3c7"/>'
              '<circle cx="-13" cy="-4" r="6" fill="#0b1b33"/><circle cx="13" cy="-4" r="6" fill="#0b1b33"/><circle cx="-11" cy="-6" r="2" fill="#fff"/><circle cx="15" cy="-6" r="2" fill="#fff"/>'
              '<path d="M-5 6 L5 6 L0 16Z" fill="#fbbf24"/>'
              '<path d="M-18 44 q18 12 36 0 M-14 56 q14 10 28 0" stroke="#9db3d6" stroke-width="3" fill="none" stroke-linecap="round"/></g>'
              '<path d="M122 150 l6 8 M134 150 l4 9 M164 150 l-4 9 M176 150 l-6 8" stroke="#fbbf24" stroke-width="4" stroke-linecap="round"/>')


def _corpo(uid):
    rede = ('<g stroke="#f9a8d4" stroke-width="1.6" opacity=".35"><path d="M40 40 L110 70 L90 130 L40 150 M110 70 L170 40 M300 50 L350 90 L320 150 L370 190 M350 90 L390 60"/></g>'
            '<g fill="#f9a8d4" opacity=".6"><circle cx="40" cy="40" r="4"/><circle cx="110" cy="70" r="4"/><circle cx="90" cy="130" r="4"/><circle cx="40" cy="150" r="4"/>'
            '<circle cx="170" cy="40" r="4"/><circle cx="300" cy="50" r="4"/><circle cx="350" cy="90" r="4"/><circle cx="320" cy="150" r="4"/><circle cx="370" cy="190" r="4"/></g>')
    return (_fundo(uid, "#35122f", "#0e0820", (200, 110, 170, "#f43f5e")) + rede
            + f'<defs><linearGradient id="h{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fb7185"/><stop offset="1" stop-color="#be123c"/></linearGradient></defs>'
              f'<path d="M200 170 C112 112 142 46 200 88 C258 46 288 112 200 170Z" fill="url(#h{uid})"/>'
              '<path d="M160 82 C170 66 188 66 196 82" stroke="#fecdd3" stroke-width="5" fill="none" stroke-linecap="round" opacity=".7"/>'
              '<polyline points="0,176 96,176 128,176 148,134 172,208 196,148 214,176 400,176" fill="none" stroke="#67e8f9" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')


def _tecnologia(uid):
    tr = ('<g stroke="#22d3ee" stroke-width="3.5" fill="none" stroke-linecap="round" opacity=".9">'
          '<path d="M155 96 H90 V54 H40"/><path d="M155 124 H70 V170 H30"/><path d="M245 96 H310 V150 H370"/>'
          '<path d="M245 126 H340 V190"/><path d="M185 65 V30"/><path d="M215 65 V30 H260"/><path d="M200 155 V200"/></g>'
          '<g fill="#06283d" stroke="#22d3ee" stroke-width="3.5"><circle cx="40" cy="54" r="6"/><circle cx="30" cy="170" r="6"/>'
          '<circle cx="370" cy="150" r="6"/><circle cx="340" cy="190" r="6"/><circle cx="260" cy="30" r="6"/><circle cx="185" cy="30" r="6"/><circle cx="200" cy="200" r="6"/></g>')
    return (_fundo(uid, "#073a5a", "#041a2e", (200, 110, 170, "#22d3ee")) + tr
            + '<rect x="155" y="65" width="90" height="90" rx="14" fill="#0c4a6e" stroke="#67e8f9" stroke-width="3"/><rect x="172" y="82" width="56" height="56" rx="8" fill="#22d3ee"/>'
              '<path d="M186 110 h28 M200 96 v28" stroke="#06283d" stroke-width="5" stroke-linecap="round"/>'
              '<g fill="none" stroke="#a5f3fc" stroke-width="4" stroke-linecap="round" opacity=".9"><path d="M312 52 a22 22 0 0 1 30 0"/><path d="M304 42 a34 34 0 0 1 46 0"/></g><circle cx="327" cy="62" r="4" fill="#a5f3fc"/>')


def _ambiente(uid):
    return (_fundo(uid, "#0a2a52", "#0a3d3a", (95, 96, 150, "#fbbf24")) + _estrelas(E1[:8], "#e0f2fe", ".7")
            + '<circle cx="95" cy="92" r="26" fill="#fde68a"/>'
              '<path d="M0 150 L70 104 L120 134 L190 82 L260 130 L320 98 L400 146 V220 H0Z" fill="#134e6b"/>'
              '<path d="M0 176 L60 138 L130 168 L210 120 L290 166 L360 132 L400 156 V220 H0Z" fill="#0f766e"/>'
              '<path d="M0 220 V200 Q90 178 160 196 T290 190 T400 184 V220Z" fill="#064e3b"/>'
              '<path d="M205 220 Q196 196 214 180 Q232 166 224 150" stroke="#67e8f9" stroke-width="9" fill="none" stroke-linecap="round" opacity=".75"/>'
              '<g fill="#052e2b"><path d="M60 196 l12 -34 l12 34z"/><path d="M82 198 l10 -28 l10 28z"/><path d="M320 192 l12 -34 l12 34z"/><path d="M344 196 l9 -26 l9 26z"/></g>')


def _fisica(uid):
    orb = "".join(f'<ellipse cx="200" cy="104" rx="84" ry="27" transform="rotate({r} 200 104)"/>' for r in (0, 60, 120))
    return (_fundo(uid, "#10286b", "#050f2c", (200, 104, 160, "#3b82f6")) + _estrelas(E1[:7], "#bfdbfe", ".6")
            + f'<g fill="none" stroke="#60a5fa" stroke-width="3.5" opacity=".95">{orb}</g>'
              '<circle cx="200" cy="104" r="17" fill="#f59e0b"/><circle cx="195" cy="99" r="5" fill="#fde68a"/>'
              '<g fill="#67e8f9"><circle cx="284" cy="104" r="7"/><circle cx="158" cy="31" r="7"/><circle cx="158" cy="177" r="7"/></g>'
              '<path d="M0 184 Q25 154 50 184 T100 184 T150 184 T200 184 T250 184 T300 184 T350 184 T400 184" fill="none" stroke="#22d3ee" stroke-width="4" stroke-linecap="round"/>'
              '<path d="M0 194 Q25 170 50 194 T100 194 T150 194 T200 194 T250 194 T300 194 T350 194 T400 194" fill="none" stroke="#3b82f6" stroke-width="3" stroke-linecap="round" opacity=".6"/>')


_CENAS = {"espaco": _espaco, "animais": _animais, "corpo": _corpo, "tecnologia": _tecnologia, "ambiente": _ambiente,
          "fisica": _fisica}


def cena(tema, uid):
    slug, _, desc = TEMAS.get(tema, TEMAS["Espaço"])
    return _svg(_CENAS[slug](uid), desc)


def marca():
    """Logotipo: um selo de conferido com uma órbita."""
    return ('<svg viewBox="0 0 40 40" width="38" height="38" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
            '<defs><linearGradient id="lm" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3b82f6"/><stop offset="1" stop-color="#22d3ee"/></linearGradient></defs>'
            '<circle cx="20" cy="20" r="17" fill="url(#lm)"/>'
            '<ellipse cx="20" cy="20" rx="19" ry="7" transform="rotate(-24 20 20)" fill="none" stroke="#e0f2fe" stroke-width="1.6" opacity=".75"/>'
            '<path d="M12.5 20.5 l5 5 l10 -11" fill="none" stroke="#04122b" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
