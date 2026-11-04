"""Monta o site da S&P: gera as imagens otimizadas e as páginas HTML.

Uso:  python tools/build.py

- src/layout.html      moldura comum (topo, menu, rodapé)
- src/paginas/*.html   conteúdo de cada página (cabeçalho "chave: valor" até a linha ---)
- src/icones/*.svg     ícones, usados com {{icone:nome}}
- _originais/          fotos originais (fora do git)

Para acrescentar fotos: ponha o arquivo em _originais/, inclua o nome na obra em OBRAS e rode de novo.
"""
import html
import os
import re

from PIL import Image, ImageOps

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(RAIZ, "_originais")
IMG = os.path.join(RAIZ, "assets", "img")
SRC = os.path.join(RAIZ, "src")
AZUL = (10, 34, 64)
DOMINIO = "https://www.spconstrutora.com/"


def faixa(a, b, ext):
    return [f"i{n:03d}.{ext}" for n in range(a, b + 1)]


# destaque = índice (a partir de 0) da foto que aparece na página inicial
OBRAS = [
    dict(id="corsan", cliente="Corsan", titulo="Estruturas de concreto armado e terraplenagem",
         fotos=faixa(47, 58, "gif"), destaque=2),
    dict(id="stihl", cliente="STIHL", titulo="Piso de concreto e pavimentação externa",
         fotos=["i036.png", "i037.png", "i038.png"] + faixa(39, 45, "jpg"), destaque=5),
    dict(id="gedore", cliente="GEDORE", titulo="Drenagem e movimentação de terra",
         fotos=faixa(72, 76, "jpg"), destaque=0),
    dict(id="bimbo", cliente="Grupo Bimbo", titulo="Cobertura metálica para passarela de pedestres",
         fotos=faixa(82, 88, "jpg"), destaque=3),
    dict(id="fitesa", cliente="Fitesa", titulo="Fundações e contenção em concreto armado",
         fotos=["i078.jpg", "i079.png", "i080.jpg"], destaque=0),
    dict(id="maiojama", cliente="Maiojama", titulo="Reforma de piso em área comercial",
         fotos=faixa(60, 66, "jpg"), destaque=6),
    dict(id="inter", cliente="Sport Club Internacional", titulo="Reforma interna com divisórias",
         fotos=faixa(68, 70, "jpg"), destaque=0),
]

LOGOS = [
    ("stihl", "STIHL", "i093.png"), ("gerdau", "Gerdau", "i094.png"), ("gedore", "GEDORE", "i097.png"),
    ("bimbo", "Grupo Bimbo", "i098.png"), ("ge", "GE", "i107.png"), ("corsan", "Corsan", None),
    ("bunge", "Bunge", "i103.png"), ("iff", "IFF", "i091.png"), ("fitesa", "Fitesa", "i105.png"),
    ("inbetta", "InBetta", "i096.png"), ("midea", "Midea", "i102.png"), ("sulzer", "Sulzer", "i104.png"),
    ("prometeon", "Prometeon", "i100.png"), ("tfl", "TFL", "i099.png"), ("lansul", "Lansul", "i106.png"),
    ("maiojama", "Maiojama", "i101.png"), ("moinhos", "Hospital Moinhos de Vento", "i095.png"),
    ("inter", "Sport Club Internacional", "i092.png"),
]

# (arquivo de saída, original, largura, altura de recorte ou None, ponto focal x/y de 0 a 1)
AVULSAS = [
    ("banner-empresa", "i076.jpg", 1920, 560, (0.5, 0.6)),
    ("banner-servicos", "i047.gif", 1920, 560, (0.5, 0.62)),
    ("banner-portfolio", "i058.gif", 1920, 560, (0.5, 0.55)),
    ("banner-clientes", "i062.jpg", 1920, 560, (0.5, 0.5)),
    ("banner-contato", "i085.jpg", 1920, 560, (0.5, 0.55)),
    ("fundo-numeros", "i049.gif", 1920, 900, (0.5, 0.7)),
    ("industria", "i080.jpg", 1300, 1400, (0.4, 0.5)),
    ("industria-2", "i041.jpg", 1200, 960, (0.5, 0.4)),
    ("industria-larga", "i041.jpg", 1920, 900, (0.5, 0.36)),
    ("sobre-1", "i080.jpg", 900, 1000, (0.42, 0.5)),
    ("sobre-2", "i041.jpg", 600, 600, (0.5, 0.35)),
    ("serv-execucao", "i053.gif", 900, 640, (0.5, 0.55)),
    ("serv-manutencao", "i030.jpg", 900, 640, (0.5, 0.5)),
    ("serv-reformas", "i070.jpg", 900, 640, (0.5, 0.5)),
    ("serv-projetos", "i049.gif", 900, 640, (0.5, 0.65)),
    ("serv-gerenciamento", "i066.jpg", 900, 640, (0.55, 0.5)),
]


def abrir(nome):
    return ImageOps.exif_transpose(Image.open(os.path.join(ORIG, nome)))


def salvar(im, destino, largura, q=76):
    # arquivo já gerado não é refeito; apague-o de assets/img para forçar
    if os.path.exists(destino):
        with Image.open(destino) as pronto:
            return pronto.size
    im = im.convert("RGB")
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    im.save(destino, "WEBP", quality=q, method=4)
    return im.size


def fotos_das_obras():
    for o in OBRAS:
        o["itens"] = []
        for n, nome in enumerate(o["fotos"], 1):
            base = f"obras/{o['id']}-{n:02d}"
            pequena, grande = os.path.join(IMG, base + "-640.webp"), os.path.join(IMG, base + "-1600.webp")
            im = None if os.path.exists(pequena) and os.path.exists(grande) else abrir(nome)
            salvar(im, pequena, 640)
            w, h = salvar(im, grande, 1600, q=78)
            o["itens"].append(dict(base=base, w=w, h=h))


def avulsas():
    for nome, orig, w, h, foco in AVULSAS:
        destino = os.path.join(IMG, nome + ".webp")
        if os.path.exists(destino):
            continue
        im = ImageOps.fit(abrir(orig).convert("RGB"), (w, h), Image.LANCZOS, centering=foco)
        im.save(destino, "WEBP", quality=74, method=4)
        if w >= 1900 and nome.startswith("slide"):
            im.resize((960, round(h * 960 / w)), Image.LANCZOS).save(
                os.path.join(IMG, nome + "-960.webp"), "WEBP", quality=72, method=4)
    og = os.path.join(IMG, "compartilhar.jpg")
    if not os.path.exists(og):
        ImageOps.fit(abrir("i051.gif").convert("RGB"), (1200, 630), Image.LANCZOS).save(og, quality=82)


# marcas brancas que vinham "queimadas" na foto de abertura do site antigo, na ordem em que aparecem
LOGOS_CAPA = ["Grupo Bimbo", "InBetta", "Sport Club Internacional", "STIHL", "GE", "Corsan", "IFF",
              "Hospital Moinhos de Vento", "TFL", "GEDORE"]


# versões menores para o celular (srcset); geradas a partir do .webp já pronto
REDUZIDAS = {"industria-larga": (960, 1280), "sp-branco": (260,),
             **{f"serv-{n}": (480, 720) for n in ("execucao", "manutencao", "reformas", "projetos", "gerenciamento")}}


def reduzidas():
    for nome, larguras in REDUZIDAS.items():
        with Image.open(os.path.join(IMG, nome + ".webp")) as im:
            im.load()
        for w in larguras:
            destino = os.path.join(IMG, f"{nome}-{w}.webp")
            if not os.path.exists(destino):
                im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
                    destino, "WEBP", quality=95 if im.mode == "RGBA" else 74, method=6)


def capa():
    """Separa a foto de abertura original (i002) em foto limpa + uma imagem por marca de cliente."""
    import numpy as np
    from PIL import ImageFilter

    destino = os.path.join(IMG, "capa.webp")
    if os.path.exists(destino):
        return
    orig = abrir("i002.jpg").convert("RGB")
    cinza = np.asarray(orig.convert("L"), dtype=np.float32)
    y0, y1 = 780, 866
    # onde estão as marcas: colunas claras dentro da faixa inferior
    claro = (cinza[y0:y1] > 110).any(axis=0)
    trechos, ini = [], None
    for x, c in enumerate(list(claro) + [False]):
        if c and ini is None:
            ini = x
        if not c and ini is not None:
            if trechos and ini - trechos[-1][1] < 34:
                trechos[-1] = (trechos[-1][0], x)
            else:
                trechos.append((ini, x))
            ini = None
    if len(trechos) != len(LOGOS_CAPA):
        raise SystemExit(f"capa: esperava {len(LOGOS_CAPA)} marcas, achei {len(trechos)}")
    os.makedirs(os.path.join(IMG, "capa"), exist_ok=True)
    for n, (x0, x1) in enumerate(trechos, 1):
        parte = cinza[y0:y1, x0 - 5:x1 + 5]
        alfa = np.clip((parte - 30) / 140, 0, 1) * 255
        marca = Image.new("RGBA", (parte.shape[1], parte.shape[0]), (255, 255, 255, 0))
        marca.putalpha(Image.fromarray(alfa.astype("uint8")))
        recortar_alfa(marca).save(os.path.join(IMG, "capa", f"marca-{n:02d}.webp"), "WEBP", quality=95, method=6)

    # apaga as marcas da foto, preenchendo com a vizinhança desfocada
    mascara = np.zeros_like(cinza)
    mascara[y0 - 4:y1 + 4, 200:1840] = (cinza[y0 - 4:y1 + 4, 200:1840] > 24)
    mascara = np.asarray(Image.fromarray((mascara * 255).astype("uint8")).filter(ImageFilter.MaxFilter(17)), dtype=np.float32) / 255
    livre = Image.fromarray(((1 - mascara) * 255).astype("uint8"))
    peso = np.asarray(livre.filter(ImageFilter.GaussianBlur(28)), dtype=np.float32) / 255 + 1e-4
    rgb = np.asarray(orig, dtype=np.float32)
    fundo = np.stack([
        np.asarray(Image.fromarray((rgb[..., c] * (1 - mascara)).astype("uint8")).filter(ImageFilter.GaussianBlur(28)), dtype=np.float32) / peso
        for c in range(3)], axis=-1)
    suave = np.asarray(Image.fromarray((mascara * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(4)), dtype=np.float32)[..., None] / 255
    limpa = Image.fromarray(np.clip(rgb * (1 - suave) + fundo * suave, 0, 255).astype("uint8"))
    limpa.save(destino, "WEBP", quality=82, method=4)
    limpa.resize((1100, round(919 * 1100 / 2048)), Image.LANCZOS).save(os.path.join(IMG, "capa-1100.webp"), "WEBP", quality=78, method=4)


def bloco_capa_marcas(raiz):
    itens = []
    for n, nome in enumerate(LOGOS_CAPA, 1):
        with Image.open(os.path.join(IMG, "capa", f"marca-{n:02d}.webp")) as im:
            w, h = im.size
        itens.append(f'<li><img src="{raiz}assets/img/capa/marca-{n:02d}.webp" width="{w}" height="{h}" style="--h: {h}" alt="{e(nome)}"></li>')
    # segunda volta, só para a faixa correr sem emenda no celular
    itens += [i.replace("<li>", '<li class="copia" aria-hidden="true">').replace(f'alt="{e(n)}"', 'alt=""')
              for i, n in zip(list(itens), LOGOS_CAPA)]
    return "\n".join(itens)


def recortar_alfa(im):
    im = im.convert("RGBA")
    caixa = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(caixa) if caixa else im


def logos():
    os.makedirs(os.path.join(IMG, "clientes"), exist_ok=True)
    for chave, _, arq in LOGOS:
        destino = os.path.join(IMG, "clientes", chave + ".webp")
        if os.path.exists(destino):
            continue
        if arq:
            im = recortar_alfa(abrir(arq))
        else:
            # Corsan só existe no site antigo como marca cinza-clara sobre branco: vira máscara
            base = abrir("i046.png").convert("L").crop((0, 0, 500, 180))
            alfa = base.point(lambda v: max(0, min(255, round((250 - v) * 255 / 22))))
            im = Image.new("RGBA", base.size, (70, 78, 90, 255))
            im.putalpha(alfa)
            im = recortar_alfa(im)
        im.thumbnail((360, 200), Image.LANCZOS)
        im.save(destino, "WEBP", quality=90, method=6)

    marca = recortar_alfa(abrir("i003.png"))
    marca.thumbnail((400, 400), Image.LANCZOS)
    marca.save(os.path.join(IMG, "sp-branco.webp"), "WEBP", quality=95, method=6)
    azul = Image.new("RGBA", marca.size, AZUL + (255,))
    azul.putalpha(marca.getchannel("A"))
    azul.save(os.path.join(IMG, "sp-azul.webp"), "WEBP", quality=95, method=6)
    for lado, nome in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (512, "icone-512.png")):
        fundo = Image.new("RGBA", (lado, lado), AZUL + (255,))
        m = marca.copy()
        m.thumbnail((round(lado * 0.72), round(lado * 0.72)), Image.LANCZOS)
        fundo.alpha_composite(m, ((lado - m.width) // 2, (lado - m.height) // 2))
        fundo.convert("RGB").save(os.path.join(IMG, nome))


# ---------------------------------------------------------------- blocos gerados

def e(texto):
    return html.escape(texto, quote=True)


def item_portfolio(o, n, item, raiz):
    return (
        f'<a class="pf-item revelar" href="{raiz}assets/img/{item["base"]}-1600.webp" data-cliente="{o["id"]}" '
        f'data-legenda="{e(o["cliente"])}: {e(o["titulo"])}" data-w="{item["w"]}" data-h="{item["h"]}">'
        f'<img src="{raiz}assets/img/{item["base"]}-640.webp" width="640" height="{round(640 * item["h"] / item["w"])}" '
        f'loading="lazy" decoding="async" alt="Obra da S&amp;P para {e(o["cliente"])}, foto {n}">'
        f'<span class="pf-item__capa"><span class="pf-item__lupa">{{{{icone:zoom-in}}}}</span>'
        f'<strong>{e(o["cliente"])}</strong><small>{e(o["titulo"])}</small></span></a>'
    )


def bloco_portfolio_home(raiz):
    return "\n".join(item_portfolio(o, o["destaque"] + 1, o["itens"][o["destaque"]], raiz) for o in OBRAS[:6])


def bloco_portfolio_completo(raiz):
    return "\n".join(item_portfolio(o, n, it, raiz) for o in OBRAS for n, it in enumerate(o["itens"], 1))


def bloco_filtros(raiz):
    botoes = ['<button class="filtro ativo" type="button" data-filtro="todos">Todas</button>']
    botoes += [f'<button class="filtro" type="button" data-filtro="{o["id"]}">{e(o["cliente"])}</button>' for o in OBRAS]
    return "\n".join(botoes)


def _logo(chave, nome, raiz):
    with Image.open(os.path.join(IMG, "clientes", chave + ".webp")) as im:
        w, h = im.size
    return f'<img src="{raiz}assets/img/clientes/{chave}.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{e(nome)}">'


def bloco_logos_carrossel(raiz):
    itens = "".join(f"<li>{_logo(c, n, raiz)}</li>" for c, n, _ in LOGOS)
    copia = "".join(f'<li aria-hidden="true">{_logo(c, "", raiz)}</li>' for c, n, _ in LOGOS)
    return f'<ul class="logos-trilho">{itens}{copia}</ul>'


def bloco_logos_grade(raiz):
    return "\n".join(f'<li class="revelar">{_logo(c, n, raiz)}</li>' for c, n, _ in LOGOS)


BLOCOS = {
    "portfolio_home": bloco_portfolio_home, "portfolio_completo": bloco_portfolio_completo,
    "filtros": bloco_filtros, "logos_carrossel": bloco_logos_carrossel, "logos_grade": bloco_logos_grade,
    "capa_marcas": bloco_capa_marcas,
}


def icone(nome):
    svg = open(os.path.join(SRC, "icones", nome + ".svg"), encoding="utf-8").read()
    svg = re.sub(r"\s+", " ", svg)
    svg = re.sub(r' class="[^"]*"', ' class="ic" aria-hidden="true" focusable="false"', svg, count=1)
    return svg.replace('<path stroke="none" d="M0 0h24v24H0z" fill="none"/>', "").strip()


def ler_pagina(arquivo):
    texto = open(os.path.join(SRC, "paginas", arquivo), encoding="utf-8").read()
    cabeca, corpo = texto.split("\n---\n", 1)
    meta = {k.strip(): v.strip() for k, _, v in (l.partition(":") for l in cabeca.strip().splitlines())}
    return meta, corpo


def paginas():
    layout = open(os.path.join(SRC, "layout.html"), encoding="utf-8").read()
    urls = []
    for arquivo in sorted(os.listdir(os.path.join(SRC, "paginas"))):
        meta, corpo = ler_pagina(arquivo)
        caminho = meta.get("caminho", "")
        raiz = "/" if arquivo == "404.html" else "../" * caminho.count("/")
        pagina = layout.replace("{{conteudo}}", corpo)
        pagina = re.sub(r"\{\{bloco:(\w+)\}\}", lambda m: BLOCOS[m.group(1)](raiz), pagina)
        pagina = re.sub(r"\{\{ativo:([\w-]*)\}\}",
                        lambda m: ' class="ativo" aria-current="page"' if m.group(1) == meta["menu"] else "", pagina)
        pagina = re.sub(r"\{\{icone:([\w-]+)\}\}", lambda m: icone(m.group(1)), pagina)
        for chave, valor in dict(meta, raiz=raiz, inicio=raiz or "./", url=DOMINIO + caminho).items():
            pagina = pagina.replace("{{" + chave + "}}", valor)
        sobra = re.search(r"\{\{[^}]+\}\}", pagina)
        if sobra:
            raise SystemExit(f"{arquivo}: marcador sem valor {sobra.group(0)}")
        destino = os.path.join(RAIZ, caminho, "404.html" if arquivo == "404.html" else "index.html")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        open(destino, "w", encoding="utf-8", newline="\n").write(pagina)
        if arquivo != "404.html":
            urls.append(DOMINIO + caminho)
    return urls


def redirecionamentos():
    # endereços do site antigo (Google Sites) que mudaram de nome
    for pasta, novo in {"inicio": "", "serviços": "servicos/", "portifólio": "portfolio/", "portifolio": "portfolio/"}.items():
        os.makedirs(os.path.join(RAIZ, pasta), exist_ok=True)
        open(os.path.join(RAIZ, pasta, "index.html"), "w", encoding="utf-8", newline="\n").write(
            f'<!doctype html>\n<html lang="pt-BR">\n<head>\n  <meta charset="utf-8">\n  <title>S&amp;P Engenharia e Construção</title>\n'
            f'  <meta name="robots" content="noindex">\n  <link rel="canonical" href="{DOMINIO}{novo}">\n'
            f'  <meta http-equiv="refresh" content="0; url=../{novo}">\n</head>\n'
            f'<body><p><a href="../{novo}">Continuar para o site da S&amp;P Engenharia e Construção</a></p></body>\n</html>\n')


def main():
    fotos_das_obras()
    avulsas()
    capa()
    logos()
    reduzidas()
    urls = paginas()
    redirecionamentos()
    open(os.path.join(RAIZ, "sitemap.xml"), "w", newline="\n").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    total = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(IMG) for f in fs)
    print(f"{len(urls)} paginas, {sum(len(o['itens']) for o in OBRAS)} fotos, {len(LOGOS)} logos, {total / 1e6:.1f} MB de imagens")


if __name__ == "__main__":
    main()
