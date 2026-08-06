# -*- coding: utf-8 -*-
"""Proposta comercial D'Coratto — A4 retrato, linguagem editorial.

Conceito grafico:
  · coluna de marginalia a esquerda, com fio vertical continuo e kicker rotacionado
  · numeral fantasma em Lora, atras do titulo, como marca d'agua tipografica
  · fios de cabelo no lugar de caixas preenchidas
  · arco em creme como painel de fundo (nunca recorta o render)
  · assimetria controlada: texto sempre na coluna direita, respiro a esquerda
"""
import os
import json
from PIL import Image, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_BASE = os.path.dirname(os.path.abspath(__file__))
# Aceita os dois layouts: com pasta assets/ ou tudo solto na raiz.
_A = os.path.join(_BASE, 'assets')
_ROOT_ASSETS = not os.path.isdir(_A)
AS_DIR = _BASE if _ROOT_ASSETS else _A
GF_DIR = AS_DIR if _ROOT_ASSETS or not os.path.isdir(os.path.join(_A, 'fonts')) \
         else os.path.join(_A, 'fonts')
GF = GF_DIR + os.sep
pdfmetrics.registerFont(TTFont('Lora', GF + 'Lora-Variable.ttf'))
pdfmetrics.registerFont(TTFont('LoraIt', GF + 'Lora-Italic-Variable.ttf'))
pdfmetrics.registerFont(TTFont('Pop', GF + 'Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('PopL', GF + 'Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('PopM', GF + 'Poppins-Medium.ttf'))

W, H = 595.0, 842.0
MG = 46.0          # faixa de marginalia
FIO = 74.0         # x do fio vertical
TX = 96.0          # inicio da coluna de texto
RM = 50.0          # margem direita
CW = W - TX - RM   # 449

UP = os.environ.get('DCO_UPLOADS', './uploads/')
AS = AS_DIR + os.sep
TMP = os.environ.get('DCO_TMP', './_tmp/')
os.makedirs(TMP, exist_ok=True)

CHAR = (0x35 / 255, 0x36 / 255, 0x3A / 255)
BRONZE = (0xA7 / 255, 0x72 / 255, 0x3B / 255)
CREAM = (0xF4 / 255, 0xF1 / 255, 0xEC / 255)
SAND = (0xE9 / 255, 0xE3 / 255, 0xDA / 255)
LINE = (0.85, 0.84, 0.82)
GREY = (0.45, 0.45, 0.47)
MID = (0.30, 0.30, 0.32)
WHITE = (1, 1, 1)

# ------------------------------- DADOS -------------------------------


def gerar(dados, saida):
    """Gera o PDF da proposta. `dados` e um dict; `saida` e caminho do arquivo."""
    import os as _os
    _os.makedirs(TMP, exist_ok=True)

    CLIENTE = dados['cliente']
    PROPOSTA = dados.get('proposta') or ''
    DATA = dados['data']
    VALIDADE = dados.get('validade') or '10 dias'
    PAGAMENTO = dados.get('pagamento') or ''
    NPARC = int(dados.get('parcelas') or 12)
    PRAZO = dados.get('prazo') or ''
    CONTATO = ''

    AMBIENTES = []
    for i, a in enumerate(dados['ambientes']):
        num = f'{i + 1:02d}'
        AMBIENTES.append((num, a['nome'], float(a['valor']),
                          (float(a['parcela']) if a.get('parcela') else None),
                          a.get('desc', ''), list(a.get('fotos', []))))
    TOTAL = sum(a[2] for a in AMBIENTES)
    # Parcela do total. A equipe costuma informar o parcelamento so no valor
    # final — antes eu exigia parcela em TODOS os ambientes e, faltando uma, a
    # linha "ou Nx de" sumia inteira.
    _parcs = [a[3] for a in AMBIENTES]
    TOTAL_PARC = dados.get('parcela_total') or None
    if not TOTAL_PARC and _parcs and all(p for p in _parcs):
        TOTAL_PARC = sum(_parcs)

    ARQ = dados.get('arquiteto') or {'tipo': 'nenhum'}
    # arquiteto pediu exclusividade: a grade da rede nao entra
    SO_ESTE_ARQ = bool(ARQ.get('exclusivo'))

    # foto de fundo para capa/divisor/encerramento: 1a foto do 1o ambiente com foto
    _fundo = None
    for a in AMBIENTES:
        if a[5]:
            _fundo = a[5][0]
            break
    if not _fundo:
        _fundo = AS + 'embaixador.jpg'


    DIF1 = [
        ('dif_umidade.jpg', 'Proteção contra a umidade',
         'Costas de 6mm revestidas em ambas as faces e recuadas 16mm, protegendo do contato direto '
         'com a umidade das paredes. Todas as bordas em contato com superfícies são fitadas.'),
        ('dif_borda.jpg', 'Resistência da fita borda',
         'Fita de 1mm aplicada com cola PUR — acabamento superior às colas convencionais, com alta '
         'aderência e resistência à umidade e a altas temperaturas.'),
        ('dif_carga.jpg', 'Carga máxima de 100kg',
         'Fixação discreta por cantoneiras metálicas embutidas nas costas dos módulos, suportando '
         'até 100kg por armário — 50kg por cantoneira.'),
        ('dif_vidro.jpg', 'Portas de vidro próprias',
         'Fabricação própria de portas de alumínio, com maior flexibilidade de edição, modelos e '
         'acabamentos — tanto em vidros quanto em perfis.'),
    ]
    DIF2 = [
        ('dif_laca.jpg', 'Laca e frentes usinadas',
         'Cava, provençal e cobogó em pintura laca nos acabamentos brilho, fosco, metalizado e '
         'aveludado. Usinagem sem emendas aparentes.'),
        ('dif_recorte.jpg', 'Painéis com recortes especiais',
         'De um tampo usinado a desenhos geométricos, cobogós e treliças — liberdade total de '
         'personalização.'),
        ('dif_curvo.jpg', 'Painel curvo',
         'Forma orgânica e suave, disponível em versão ripada ou lisa, em medidas padrão ou no '
         'modelo ripado moldável.'),
        ('dif_ripado.jpg', 'Painel ripado',
         'Movimento e naturalidade com instalação simples: os painéis saem prontos de fábrica.'),
    ]
    DIF_TXT = [
        ('Marmoraria própria', 'Marcenaria e superfícies pela mesma casa — medidas compatibilizadas e um só responsável.'),
        ('Sistemas de abertura', 'Aventos, Free Fold e Free Flap Häfele, Articulador Maxi, pistão a gás, click, deslizante e coplanar.'),
        ('Linha Grass e Kessebohmer', 'Gavetas metálicas com deslizamento oculto e acessórios aramados importados da Alemanha.'),
        ('Iluminação integrada', 'LED interno e externo com acendimento por sensor de presença, de gesto ou de porta.'),
    ]
    MATERIAIS = [
        ('Madeiras em laminado', 'Melanina na superfície, fundos de 6 mm, caixaria de 15 mm e tamponamentos de 35 mm.'),
        ('Fita de borda', 'Fita vulcânica de 1mm aplicada com cola PUR — fusão perfeita ao painel, sem emendas visíveis.'),
        ('Ferragens', 'Dobradiça inoxidável com slow, corrediças ocultas com amortecimento, suportando até 45 kg.'),
        ('Fixação', 'Cantoneiras metálicas embutidas nas costas dos módulos, suportando até 100kg por armário.'),
    ]
    CLIENTES = [('Thiago Miranda', '@thiagomiranda01'), ('Sandra Redivo', '@sanredivo'),
                ('Valéria Pacheco', '@valeriapachecocoelho'), ('Bia Hulmann', '@biahulmann')]
    # (nome, @, arquivo da foto) na ordem definida pela D'Coratto. O arquivo vai
    # explicito para o nome nunca depender da posicao — era isso que causava a
    # troca de nome com foto.
    _ARQ_ORDEM = [
        ('Tamyres Marques', '@tamyarquiteta', 'arq_3.jpg'),
        ('Luana Inaimo', '@arq.luinaimo', 'arq_luana.jpg'),
        ('Felipe Vale Lopes', '@angararquitetura', 'arq_felipe.jpg'),
        ('Bianca Jurtick', '@aconstrutora.br', 'arq_4.jpg'),
        ('Caique Nogueira', '@arquiteto.caiquenogueira', 'arq_caique.jpg'),
        ('Karin Martins', '@km_arqdesigner', 'arq_km.jpg'),
        ('Eng. Kethelyn', '@legus.engenharia', 'arq_1.jpg'),
        ('Eduardo Felipe', '@aha_arquitetura', 'arq_eduardo.jpg'),
        ('Jornate Obras', '@jornateobras', 'arq_2.jpg'),
    ]
    # so entra quem tem a foto de fato no disco (evita quebrar a geracao)
    ARQUITETOS = [t for t in _ARQ_ORDEM if os.path.exists(AS + t[2])]
    PARCEIROS = json.load(open(AS + 'parceiros.json'))


    # ------------------------------ HELPERS ------------------------------
    def brl(v):
        return 'R$ ' + f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


    def cover(path, w, h, key, focus=0.5, darken=None):
        out = TMP + key + '.jpg'
        im = Image.open(path).convert('RGB')
        sw, sh = im.size
        tr, sr = w / h, sw / sh
        if sr > tr:
            nw = int(sh * tr)
            x = int((sw - nw) * 0.5)
            im = im.crop((x, 0, x + nw, sh))
        else:
            nh = int(sw / tr)
            y = int((sh - nh) * focus)
            im = im.crop((0, y, sw, y + nh))
        im = im.resize((int(w * 2.6), int(h * 2.6)), Image.LANCZOS)
        if darken:
            im = ImageEnhance.Brightness(im).enhance(darken)
        im.save(out, quality=86)
        return out


    def contain(path, boxw, boxh, key):
        im = Image.open(path).convert('RGB')
        sw, sh = im.size
        r = min(boxw / sw, boxh / sh)
        w, h = sw * r, sh * r
        out = TMP + key + '.jpg'
        im.resize((max(1, int(w * 2.6)), max(1, int(h * 2.6))), Image.LANCZOS).save(out, quality=88)
        return out, w, h


    def wrap(text, font, size, maxw):
        lines, cur = [], ''
        for wd in text.split():
            t = (cur + ' ' + wd).strip()
            if pdfmetrics.stringWidth(t, font, size) <= maxw:
                cur = t
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


    def para(c, text, x, y, font, size, lead, maxw, color=MID):
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        for ln in wrap(text, font, size, maxw):
            c.drawString(x, y, ln)
            y -= lead
        return y


    def tracked(c, text, x, y, font, size, track, color=CHAR):
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        for ch in text:
            c.drawString(x, y, ch)
            x += pdfmetrics.stringWidth(ch, font, size) + track
        return x


    def fio(c, x1, x2, y, color=LINE, wd=0.5):
        c.setStrokeColorRGB(*color)
        c.setLineWidth(wd)
        c.line(x1, y, x2, y)


    def fio_vertical(c, x, y1, y2, color=LINE, wd=0.5):
        c.setStrokeColorRGB(*color)
        c.setLineWidth(wd)
        c.line(x, y1, x, y2)


    def marginalia(c, texto, escuro=False):
        """Fio vertical continuo + kicker rotacionado na coluna esquerda."""
        col = (0.42, 0.42, 0.44) if escuro else LINE
        fio_vertical(c, FIO, 78, H - 62, col, 0.5)
        c.saveState()
        c.translate(MG + 14, 84)
        c.rotate(90)
        tracked(c, texto, 0, 0, 'PopM', 7, 3.2, BRONZE)
        c.restoreState()


    def ghost(c, texto, x, y, size=112):
        c.setFont('Lora', size)
        c.setFillColorRGB(*CREAM)
        c.drawRightString(x, y, texto)


    def _ajusta_titulo(txt, fonte, tam, maxw, min_tam=15.0, max_linhas=2):
        """Devolve (linhas, tamanho) que cabem em maxw.

        Antes o titulo era desenhado em tamanho fixo e o que passava da coluna
        era simplesmente cortado na borda da pagina — nomes longos de ambiente
        saiam pela metade. Aqui ele primeiro quebra em ate duas linhas e, se
        ainda nao couber, reduz a fonte ate caber.
        """
        t = tam
        while t >= min_tam:
            linhas = wrap(txt, fonte, t, maxw)
            if len(linhas) <= max_linhas and all(
                    pdfmetrics.stringWidth(l, fonte, t) <= maxw for l in linhas):
                return linhas, t
            t -= 0.5
        linhas = wrap(txt, fonte, min_tam, maxw)[:max_linhas]
        return linhas, min_tam


    def cabeca(c, kicker, titulo, italico=None, y=H - 118, maxw=None):
        """Titulo editorial: numeral fantasma + titulo + fio curto.

        O titulo se adapta: quebra de linha primeiro, reducao de corpo depois.
        """
        marginalia(c, kicker)
        larg = maxw if maxw else CW
        linhas, tam = _ajusta_titulo(titulo, 'Lora', 27, larg)
        c.setFillColorRGB(*CHAR)
        c.setFont('Lora', tam)
        for i, ln in enumerate(linhas):
            c.drawString(TX, y - i * (tam * 1.18), ln)
        y -= (len(linhas) - 1) * (tam * 1.18)
        if italico:
            lin2, tam2 = _ajusta_titulo(italico, 'LoraIt', 27, larg)
            c.setFillColorRGB(*BRONZE)
            c.setFont('LoraIt', tam2)
            for i, ln in enumerate(lin2):
                c.drawString(TX, y - 32 - i * (tam2 * 1.18), ln)
            y -= 32 + (len(lin2) - 1) * (tam2 * 1.18)
        fio(c, TX, TX + 38, y - 18, BRONZE, 1.1)
        return y - 48


    def arco(c, x, y, w, h, cor=CREAM):
        """Painel em arco (topo abaulado) usado como fundo — nunca corta imagem.

        O raio e limitado a altura. Sem esse limite, um painel mais baixo que w/2
        fazia o caminho passar ABAIXO do ponto inicial e a forma se autointersectava,
        produzindo uma cunha branca torta atravessando o bege.
        """
        r = min(w / 2.0, h)
        p = c.beginPath()
        p.moveTo(x, y)
        p.lineTo(x, y + h - r)
        p.arcTo(x, y + h - 2 * r, x + w, y + h, 0, 180)
        p.lineTo(x + w, y)
        p.close()
        c.setFillColorRGB(*cor)
        c.drawPath(p, fill=1, stroke=0)


    def render(c, path, x, y, boxw, boxh, key, arco_fundo=True):
        """Render completo, sem recorte, sobre painel em arco."""
        f, w, h = contain(path, boxw, boxh, key)
        ix = x + (boxw - w) / 2
        if arco_fundo:
            aw = w + 26
            arco(c, ix - 13, y - 14, aw, h + 34)
        c.drawImage(f, ix, y, w, h)
        fio(c, ix, ix + w, y - 6, LINE, 0.5)
        return w, h


    PAG = [0]


    def fecha(c, escuro=False, numerar=True):
        PAG[0] += 1
        if numerar:
            col = (0.6, 0.6, 0.62) if escuro else (0.55, 0.55, 0.57)
            c.setFont('PopL', 6.4)
            c.setFillColorRGB(*col)
            c.drawString(TX, 56, 'D’CORATTO SOB MEDIDA')
            c.drawCentredString(W / 2 + 24, 56, 'Proposta comercial · ' + CLIENTE)
            c.setFont('Lora', 9)
            c.setFillColorRGB(*BRONZE)
            c.drawRightString(W - RM, 56, f'{PAG[0]:02d}')
        c.showPage()


    c = canvas.Canvas(saida, pagesize=(W, H))
    c.setTitle('Proposta Comercial – João Carlos – D’Coratto Sob Medida')
    c.setAuthor('D’Coratto Sob Medida')

    # =============================== CAPA ===============================
    c.drawImage(cover(_fundo, W, H, 'capa', focus=0.30, darken=0.58), 0, 0, W, H)
    # véu inferior em degradê simulado por faixas
    for i in range(60):
        t = i / 59.0
        c.setFillColorRGB(CHAR[0], CHAR[1], CHAR[2], alpha=t * 0.97)
        c.rect(0, 300 - i * 5, W, 6, fill=1, stroke=0)
    c.setFillColorRGB(*CHAR)
    c.rect(0, 0, W, 8, fill=1, stroke=0)
    c.setFillColorRGB(CHAR[0], CHAR[1], CHAR[2], alpha=0.97)
    c.rect(0, 0, W, 130, fill=1, stroke=0)

    c.drawImage(ImageReader(AS + 'logo.png'), TX, H - 132, 160, 78, mask='auto')
    fio_vertical(c, FIO, 96, H - 68, (0.55, 0.5, 0.44), 0.6)

    c.saveState()
    c.translate(MG + 14, 100)
    c.rotate(90)
    tracked(c, 'PROPOSTA COMERCIAL  ·  ' + DATA, 0, 0, 'PopM', 7, 3.2, (0.78, 0.68, 0.55))
    c.restoreState()

    c.setFont('Lora', 34)
    c.setFillColorRGB(*WHITE)
    c.drawString(TX, 196, 'Móveis sob medida')
    c.setFont('LoraIt', 34)
    c.setFillColorRGB(0.85, 0.72, 0.55)
    c.drawString(TX, 156, 'projetados para você')
    fio(c, TX, TX + 38, 134, BRONZE, 1.1)
    c.setFont('PopL', 7)
    c.setFillColorRGB(0.62, 0.62, 0.64)
    c.drawString(TX, 92, 'CLIENTE')
    c.setFont('Lora', 15)
    c.setFillColorRGB(*WHITE)
    c.drawString(TX, 72, CLIENTE)
    c.setFont('PopL', 7)
    c.setFillColorRGB(0.55, 0.55, 0.57)
    c.drawRightString(W - RM, 72, f'{PROPOSTA}  ·  válida por {VALIDADE}')
    fecha(c, numerar=False)

    # ============================ A D'CORATTO ============================
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '01', W - RM, H - 150)
    y = cabeca(c, 'QUEM SOMOS', 'A D’Coratto')
    for t in [
        'Nasce do encontro entre o desejo de criar ambientes únicos e a obsessão por entregar um '
        'trabalho que honre a confiança de cada cliente. Há 8 anos no mercado, em Mogi das Cruzes, '
        'consolidamos nosso nome como referência em projetos personalizados de alto padrão.',
        'Muito mais que uma marcenaria, somos um ecossistema de criação. Do primeiro atendimento à '
        'instalação final, cada detalhe é acompanhado de perto — com marmoraria própria e linha '
        'completa de acabamentos especiais, entregamos soluções completas e integradas.',
        'Acreditamos que o segredo está na escuta. É ouvindo com atenção que traduzimos desejos em '
        'projetos sob medida: na matéria-prima, na inteligência dos layouts, no toque das texturas '
        'e na sutileza das cores que compõem cada ambiente.',
    ]:
        y = para(c, t, TX, y, 'PopL', 9.2, 15.5, CW) - 15

    fio(c, TX, W - RM, y + 4, LINE, 0.5)
    c.setFont('LoraIt', 17)
    c.setFillColorRGB(*CHAR)
    c.drawString(TX, y - 26, 'Mais do que móveis, entregamos')
    c.setFont('LoraIt', 17)
    c.setFillColorRGB(*BRONZE)
    c.drawString(TX + pdfmetrics.stringWidth('Mais do que móveis, entregamos ', 'LoraIt', 17), y - 26,
                 'pertencimento.')
    c.setFont('PopL', 8)
    c.setFillColorRGB(*GREY)
    c.drawString(TX, y - 46, 'E sabemos que os detalhes fazem toda a diferença.')

    iw, ih = 300.0, 300.0
    arco(c, (W - iw) / 2, 84, iw, ih + 34, SAND)
    c.drawImage(cover(AS + 'fabril_2.jpg', iw - 40, ih, 'inst', focus=0.0), (W - iw) / 2 + 20, 100,
                iw - 40, ih)
    fecha(c)

    # ============================ PARQUE FABRIL ============================
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.drawImage(cover(AS + 'fabril_pano.jpg', W, 268, 'fabpano', focus=0.5), 0, H - 268, W, 268)
    ghost(c, '02', W - RM, H - 356)
    y = cabeca(c, 'ESTRUTURA', 'Parque fabril próprio', y=H - 330)

    c.setFont('Lora', 52)
    c.setFillColorRGB(*CHAR)
    c.drawString(TX, y - 26, '21.000')
    c.setFont('PopL', 13)
    c.setFillColorRGB(*BRONZE)
    c.drawString(TX + pdfmetrics.stringWidth('21.000', 'Lora', 52) + 12, y - 26, 'm² de área construída')
    y = para(c, 'Escala industrial, controle total do processo produtivo e previsibilidade de prazo — '
                'do corte à instalação. Estrutura que permite absorver projetos de alto padrão sem '
                'terceirizar etapas críticas.',
             TX, y - 62, 'PopL', 9.2, 15.5, CW) - 26

    fio(c, TX, W - RM, y + 8, LINE, 0.5)
    c.drawImage(cover(AS + 'fabril_2.jpg', 200, 152, 'fab2', focus=0.4), TX, y - 156, 200, 152)
    bx = TX + 218
    tracked(c, 'ATENDIMENTO', bx, y - 18, 'PopM', 7, 3, BRONZE)
    para(c, 'Todo o território nacional, com logística e equipe de instalação próprias.',
         bx, y - 36, 'PopL', 8.4, 13, W - RM - bx)
    tracked(c, 'SHOWROOM', bx, y - 86, 'PopM', 7, 3, BRONZE)
    para(c, 'Estrada da Pedreira, 554 – Parquelândia', bx, y - 104, 'PopL', 8.4, 13, W - RM - bx)
    para(c, 'Mogi das Cruzes/SP – 08771-210', bx, y - 117, 'PopL', 8.4, 13, W - RM - bx)
    fecha(c)

    # ============================ DIFERENCIAIS ============================
    def item_dif(c, img, tit, txt, y, espelhado=False, s=92.0, folga=32.0):
        """Item em duas colunas, imagem alternando de lado. Sem caixa preenchida."""
        gapc = 20.0
        tw = CW - s - gapc
        nlin = len(wrap(txt, 'PopL', 8.4, tw))
        alt = max(s, 26 + nlin * 13)
        if espelhado:
            ix, txx = TX + CW - s, TX
        else:
            ix, txx = TX, TX + s + gapc
        c.drawImage(cover(AS + img, s, s, 'd_' + img, focus=0.4), ix, y - alt + (alt - s) / 2, s, s)
        c.setFont('PopM', 10.5)
        c.setFillColorRGB(*CHAR)
        c.drawString(txx, y - 12, tit)
        para(c, txt, txx, y - 30, 'PopL', 8.4, 13, tw, MID)
        fio(c, TX, W - RM, y - alt - 12, LINE, 0.5)
        return y - alt - folga


    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '03', W - RM, H - 150)
    y = cabeca(c, 'CONHEÇA NOSSOS DIFERENCIAIS', 'O que está', 'por dentro')
    y = para(c, 'O que diferencia um móvel sob medida não aparece na foto. Aparece cinco anos depois.',
             TX, y + 10, 'LoraIt', 11.5, 16, CW, GREY) - 26
    fio(c, TX, W - RM, y + 12, LINE, 0.5)
    for i, (img, t, d) in enumerate(DIF1):
        y = item_dif(c, img, t, d, y, espelhado=(i % 2 == 1))
    fecha(c)

    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '04', W - RM, H - 150)
    y = cabeca(c, 'CONHEÇA NOSSOS DIFERENCIAIS', 'O que', 'temos')
    fio(c, TX, W - RM, y + 14, LINE, 0.5)
    for i, (img, t, d) in enumerate(DIF2):
        y = item_dif(c, img, t, d, y - 4, espelhado=(i % 2 == 1), s=76.0, folga=22.0)

    y -= 24
    # altura da faixa calculada pelo conteudo, para nunca estourar
    colw = CW / 2 - 24
    nlin_max = max(len(wrap(d, 'PopL', 7.2, colw)) for _, d in DIF_TXT)
    lin_h = 16 + nlin_max * 10
    faixa_h = 32 + 2 * lin_h + 12
    c.setFillColorRGB(*CHAR)
    c.rect(TX - 14, y - faixa_h, W - (TX - 14), faixa_h, fill=1, stroke=0)
    tracked(c, 'E AINDA TEMOS COMO OPÇÃO', TX, y - 22, 'PopM', 7, 3, (0.72, 0.62, 0.48))
    yy = y - 40
    for i, (t, d) in enumerate(DIF_TXT):
        col = i % 2
        bx = TX + col * (CW / 2)
        by = yy - (i // 2) * lin_h
        c.setFont('PopM', 8.4)
        c.setFillColorRGB(*WHITE)
        c.drawString(bx, by, t)
        para(c, d, bx, by - 12, 'PopL', 7.2, 10, colw, (0.70, 0.70, 0.72))
    fecha(c)

    # ============================ DIVISOR ============================
    c.drawImage(cover(_fundo, W, H, 'div', focus=0.4, darken=0.42), 0, 0, W, H)
    tracked(c, 'O PROJETO', TX, H - 120, 'PopM', 8, 3.4, (0.85, 0.72, 0.55))
    c.setFont('Lora', 30)
    c.setFillColorRGB(*WHITE)
    c.drawString(TX, H - 165, 'Um percurso pela')
    c.setFont('LoraIt', 30)
    c.setFillColorRGB(0.85, 0.72, 0.55)
    c.drawString(TX, H - 202, 'sua casa')
    fio(c, TX, TX + 46, H - 222, BRONZE, 1.2)
    para(c, 'Os ambientes são apresentados na mesma ordem em que serão vividos — do primeiro olhar '
            'ao entrar, à integração entre estar, jantar e cozinha.',
         TX, H - 252, 'PopL', 9.5, 15, 380, (0.88, 0.88, 0.89))
    # A lista pagina sozinha e o nome quebra: com muitos ambientes ela descia
    # para fora da folha (com 17 itens o ultimo caia em y = -436).
    _LIM_DIV = 108.0
    _LARG_NOME = W - RM - (TX + 42)

    def _abre_divisor():
        c.drawImage(cover(_fundo, W, H, 'div', focus=0.4, darken=0.42), 0, 0, W, H)
        tracked(c, 'O PROJETO · continuação', TX, H - 120, 'PopM', 8, 3.4,
                (0.85, 0.72, 0.55))
        return H - 168

    y = 500
    for n, nome, val, _, _, _ in AMBIENTES:
        _lin = wrap(nome, 'PopL', 14, _LARG_NOME)
        _alt = 46 + (len(_lin) - 1) * 19
        if y - _alt < _LIM_DIV:
            fecha(c, escuro=True)
            y = _abre_divisor()
        c.setFont('Lora', 19)
        c.setFillColorRGB(0.85, 0.72, 0.55)
        c.drawString(TX, y, n)
        c.setFont('PopL', 14)
        c.setFillColorRGB(*WHITE)
        for _i, _l in enumerate(_lin):
            c.drawString(TX + 42, y - _i * 19, _l)
        _base = y - (len(_lin) - 1) * 19
        fio(c, TX, W - RM, _base - 16, (0.5, 0.5, 0.52), 0.6)
        y = _base - 46
    fecha(c, escuro=True)

    # ============================ AMBIENTES ============================
    def prep_h(path, x, y, boxw, boxh, key):
        """Calcula imagem e arco de fundo SEM desenhar.

        O arco fica preso a celula (x, y, boxw, boxh) da propria foto. Sem esse
        limite ele transbordava 18pt acima da imagem, num vao de 14pt, e entrava
        na foto vizinha.
        """
        f, w, h = contain(path, boxw, boxh, key)
        ix = x + (boxw - w) / 2.0
        iy = y + (boxh - h) / 2.0
        ax0 = max(x, ix - 13);          ax1 = min(x + boxw, ix + w + 13)
        ay0 = max(y, iy - 12);          ay1 = min(y + boxh, iy + h + 18)
        return {'f': f, 'ix': ix, 'iy': iy, 'w': w, 'h': h,
                'ax': ax0, 'ay': ay0, 'aw': ax1 - ax0, 'ah': ay1 - ay0}


    def desenha_h(c, itens):
        """Desenha TODOS os arcos e so depois TODAS as imagens.

        A ordem importa: antes era arco1, img1, arco2, img2... e o arco de uma
        foto era pintado por cima da imagem da anterior.
        """
        for it in itens:
            arco(c, it['ax'], it['ay'], it['aw'], it['ah'])
        for it in itens:
            c.drawImage(it['f'], it['ix'], it['iy'], it['w'], it['h'])
            fio(c, it['ix'], it['ix'] + it['w'], it['iy'] - 6, LINE, 0.5)


    for n, nome, val, parc, desc, fotos in AMBIENTES:
        c.setFillColorRGB(*WHITE)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        ghost(c, n, W - RM, H - 152)
        y = cabeca(c, 'AMBIENTE ' + n, nome, maxw=CW - 96)
        # Descricao adaptativa: se for longa demais, encolhe o corpo em vez de
        # empurrar fotos e preco para fora da folha.
        _td, _ld = 9.2, 15.5
        while _td > 7.0 and len(wrap(desc, 'PopL', _td, CW)) * _ld > 132:
            _td -= 0.3
            _ld = _td * 1.68
        y = para(c, desc, TX, y + 10, 'PopL', _td, _ld, CW) - 26

        # Todas as fotos enviadas entram NESTA pagina (a que leva o preco).
        # A 1a foto do 1o ambiente tambem e reaproveitada como fundo da capa e
        # da pag. 6 — reaproveitamento, nunca substituicao.
        gap = 20.0                    # > 18pt do transbordo do arco
        hw = (CW - gap) / 2           # meia largura
        itens = []
        # As fotos ocupam o que sobrou entre a descricao e o bloco de preco.
        # Sem esse calculo, uma descricao longa jogava o preco para fora da folha.
        _ALT_PRECO = 78.0
        _LIM_PG = 96.0
        _disp = max(120.0, y - _LIM_PG - _ALT_PRECO)
        _nec = {0: 0.0, 1: 300.0, 2: 440.0, 3: 440.0}.get(len(fotos), 440.0)
        _k = min(1.0, (_disp / _nec) if _nec else 1.0)
        if not fotos:
            y = y - 20
        elif len(fotos) == 1:
            bh = 300.0 * _k
            itens.append(prep_h(fotos[0], TX, y - bh, CW, bh, f'r{n}_0'))
            y = y - bh - 32
        elif len(fotos) == 2:
            bh = 210.0 * _k
            itens.append(prep_h(fotos[0], TX, y - bh, CW, bh, f'r{n}_0'))
            itens.append(prep_h(fotos[1], TX, y - 2 * bh - gap, CW, bh, f'r{n}_1'))
            y = y - 2 * bh - gap - 28
        elif len(fotos) == 3:
            # 1 larga em cima + 2 lado a lado embaixo
            bh1, bh2 = 236.0 * _k, 184.0 * _k
            itens.append(prep_h(fotos[0], TX, y - bh1, CW, bh1, f'r{n}_0'))
            itens.append(prep_h(fotos[1], TX, y - bh1 - gap - bh2, hw, bh2, f'r{n}_1'))
            itens.append(prep_h(fotos[2], TX + hw + gap, y - bh1 - gap - bh2, hw, bh2,
                                f'r{n}_2'))
            y = y - bh1 - gap - bh2 - 28
        else:
            # 4 fotos: grade 2x2
            bh = 210.0 * _k
            for _j in range(4):
                _cx = TX + (_j % 2) * (hw + gap)
                _cy = y - (_j // 2 + 1) * bh - (_j // 2) * gap
                itens.append(prep_h(fotos[_j], _cx, _cy, hw, bh, f'r{n}_{_j}'))
            y = y - 2 * bh - gap - 28
        desenha_h(c, itens)

        fio(c, TX, W - RM, y + 4, LINE, 0.5)
        tracked(c, 'INVESTIMENTO DO AMBIENTE', TX, y - 22, 'PopM', 7, 3, BRONZE)
        c.setFont('Lora', 24)
        c.setFillColorRGB(*CHAR)
        c.drawRightString(W - RM, y - 26, brl(val))
        if parc:
            c.setFont('PopL', 8)
            c.setFillColorRGB(*GREY)
            c.drawRightString(W - RM, y - 42, f'ou {NPARC}x de {brl(parc)}')
        fecha(c)

    # ============================ INVESTIMENTO ============================
    # A tabela pagina sozinha. Antes ela assumia que tudo cabia numa folha: com
    # muitos ambientes os ultimos sumiam e — pior — o bloco de TOTAL, validade e
    # forma de pagamento nem chegava a ser desenhado.
    _LIM_BAIXO = 96.0          # nao invade o rodape
    _ALT_TOTAL = 96.0          # faixa preta do total
    _ALT_COND = 92.0           # validade + forma de pagamento

    def _abre_investimento(cont=False):
        c.setFillColorRGB(*WHITE)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        ghost(c, '$', W - RM, H - 150)
        yy = cabeca(c, 'RESUMO', 'Investimento' if not cont else 'Investimento',
                    maxw=CW - 96)
        if cont:
            c.setFont('PopL', 8)
            c.setFillColorRGB(*GREY)
            c.drawString(TX, yy + 34, 'continuação')
        c.setFont('PopM', 7)
        c.setFillColorRGB(*GREY)
        c.drawString(TX, yy + 16, 'AMBIENTE')
        c.drawRightString(W - RM, yy + 16, 'VALOR')
        fio(c, TX, W - RM, yy + 6, CHAR, 0.8)
        return yy - 18

    def _altura_linha(nome, desc):
        """Quanto a linha vai ocupar, para decidir a quebra ANTES de desenhar."""
        n_nome = len(wrap(nome, 'PopM', 12.5, CW - 170))
        n_desc = len(wrap(desc, 'PopL', 8.2, CW - 150)) if desc else 0
        return (n_nome - 1) * 15 + 20 + n_desc * 12.5 + 34

    y = _abre_investimento()
    for n, nome, val, parc, desc, fotos in AMBIENTES:
        if y - _altura_linha(nome, desc) < _LIM_BAIXO:
            fecha(c)
            y = _abre_investimento(cont=True)
        c.setFont('Lora', 30)
        c.setFillColorRGB(*SAND)
        c.drawString(TX - 42, y - 8, n)
        # nome tambem quebra em vez de invadir a coluna do valor
        _lnome = wrap(nome, 'PopM', 12.5, CW - 170)
        c.setFont('PopM', 12.5)
        c.setFillColorRGB(*CHAR)
        for _i, _l in enumerate(_lnome):
            c.drawString(TX, y - _i * 15, _l)
        c.setFont('Lora', 16)
        c.setFillColorRGB(*CHAR)
        c.drawRightString(W - RM, y, brl(val))
        if parc:
            c.setFont('PopL', 7.6)
            c.setFillColorRGB(*BRONZE)
            c.drawRightString(W - RM, y - 14, f'ou {NPARC}x de {brl(parc)}')
        y -= (len(_lnome) - 1) * 15
        yy = para(c, desc, TX, y - 20, 'PopL', 8.2, 12.5, CW - 150, GREY)
        fio(c, TX, W - RM, yy - 8, LINE, 0.5)
        y = yy - 34

    # o total e as condicoes andam juntos: se nao couberem, vao para a proxima
    if y - 56 - _ALT_TOTAL - _ALT_COND < _LIM_BAIXO:
        fecha(c)
        y = _abre_investimento(cont=True) + 18   # sem cabecalho de colunas util
    y -= 56
    c.setFillColorRGB(*CHAR)
    c.rect(TX - 14, y - 86, W - (TX - 14), 86, fill=1, stroke=0)
    tracked(c, 'INVESTIMENTO TOTAL', TX, y - 34, 'PopM', 7, 3, (0.72, 0.62, 0.48))
    c.setFont('PopL', 6.6)
    c.setFillColorRGB(0.60, 0.60, 0.62)
    c.drawString(TX, y - 50, 'Fabricação e instalação dos ambientes descritos')
    c.setFont('Lora', 30)
    c.setFillColorRGB(*WHITE)
    c.drawRightString(W - RM, y - 52, brl(TOTAL))
    if TOTAL_PARC:
        c.setFont('PopL', 8)
        c.setFillColorRGB(0.72, 0.72, 0.74)
        c.drawRightString(W - RM, y - 68, f'ou {NPARC}x de {brl(TOTAL_PARC)}')

    y -= 132
    c.setFont('PopM', 8.6)
    c.setFillColorRGB(*CHAR)
    c.drawString(TX, y, 'Validade da proposta')
    c.setFont('PopL', 8.6)
    c.setFillColorRGB(*MID)
    c.drawString(TX + 132, y, VALIDADE)
    fio(c, TX, W - RM, y - 10, LINE, 0.4)
    if PAGAMENTO:
        y -= 26
        c.setFont('PopM', 8.6)
        c.setFillColorRGB(*CHAR)
        c.drawString(TX, y, 'Forma de pagamento')
        _lns = wrap(PAGAMENTO, 'PopL', 8.6, CW - 132)[:3]
        c.setFont('PopL', 8.6)
        c.setFillColorRGB(*MID)
        for _i, _ln in enumerate(_lns):
            c.drawString(TX + 132, y - _i * 12, _ln)
        fio(c, TX, W - RM, y - 10 - (12 * (len(_lns) - 1)), LINE, 0.4)
    fecha(c)

    # ============================ MATERIAIS ============================
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '05', W - RM, H - 150)
    y = cabeca(c, 'CONDIÇÕES', 'Materiais', 'e execução')
    y = para(c, 'A qualidade de um projeto sob medida está nos componentes que ninguém vê.',
             TX, y + 10, 'LoraIt', 11.5, 16, CW, GREY) - 28

    for i, (t, d) in enumerate(MATERIAIS):
        c.setFont('Lora', 13)
        c.setFillColorRGB(*SAND)
        c.drawString(TX - 40, y - 1, f'{i + 1:02d}')
        c.setFont('PopM', 9.6)
        c.setFillColorRGB(*CHAR)
        c.drawString(TX, y, t)
        yy = para(c, d, TX, y - 16, 'PopL', 8.4, 13, CW)
        fio(c, TX, W - RM, yy - 6, LINE, 0.4)
        y = yy - 26

    y -= 4
    _ah = 150.0
    arco(c, TX, y - _ah, CW, _ah, CREAM)
    c.setFont('LoraIt', 15)
    c.setFillColorRGB(*CHAR)
    c.drawCentredString(TX + CW / 2, y - 52, 'Cuidados com a sua obra')
    para(c, 'Respeitamos o seu investimento. Toda etapa da obra é acompanhada pelo nosso líder de '
            'pós-venda, e existe a preparação de todo o ambiente para receber o material — para que '
            'seja uma obra limpa e tranquila. Utilizamos um processo de acompanhamento de vistorias '
            'com o nosso supervisor de obras, por meio de um sistema de vistorias online, que traz '
            'agilidade e documentação de toda a montagem.',
         TX + 44, y - 78, 'PopL', 8.4, 13, CW - 88)

    # Duas fotos abaixo do texto: salva-piso e vistoria no tablet.
    # Ficam sobre UM painel unico, centralizado no mesmo eixo do bloco de texto,
    # para lerem como uma composicao so — antes cada foto tinha o proprio arco e
    # os tres se misturavam.
    _fh = 118.0
    _obras = [(AS + 'obra_salvapiso.jpg', 'obr1'), (AS + 'obra_vistoria.jpg', 'obr2')]
    _prep = [contain(_c, CW, _fh, _k) for _c, _k in _obras if os.path.exists(_c)]
    if _prep:
        _gap = 18.0
        _tot = sum(it[1] for it in _prep) + _gap * (len(_prep) - 1)
        _x0 = TX + (CW - _tot) / 2.0
        _ytop = y - _ah - 24
        _base = _ytop - _fh
        arco(c, _x0 - 16, _base - 12, _tot + 32, _fh + 32, CREAM)
        _x = _x0
        for _f, _w, _h in _prep:
            c.drawImage(_f, _x, _base + (_fh - _h) / 2.0, _w, _h)
            _x += _w + _gap
    fecha(c)

    # ============================ EMPRESAS PARCEIRAS ============================
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '06', W - RM, H - 150)
    y = cabeca(c, 'REDE D’CORATTO', 'Empresas', 'parceiras')
    y = para(c, 'Marcas e instituições que caminham com a gente.',
             TX, y + 10, 'PopL', 9, 14, CW, GREY) - 30

    bw = CW / 2
    bh = 132.0
    ITENS_PARC = list(PARCEIROS) + [{'texto': ('ROCHA E BONATO', 'ADVOCACIA')}]

    for i, p in enumerate(ITENS_PARC):
        col, row = i % 2, i // 2
        bx = TX + col * bw
        by = y - row * bh
        cy = by - bh / 2

        if 'texto' in p:
            # parceiro sem logotipo: lockup tipografico
            l1, l2 = p['texto']
            c.setFont('Lora', 13)
            c.setFillColorRGB(*CHAR)
            c.drawCentredString(bx + bw / 2, cy + 4, l1)
            tracked(c, l2, bx + bw / 2 - (pdfmetrics.stringWidth(l2, 'PopL', 7.4)
                                          + 3 * (len(l2) - 1)) / 2, cy - 14, 'PopL', 7.4, 3, BRONZE)
        else:
            maxw, maxh = bw - 66, bh - 46
            r = min(maxw / p['w'], maxh / p['h'])
            lw, lh = p['w'] * r, p['h'] * r
            pw, ph = lw + 38, lh + 30
            if p['claro']:
                c.setFillColorRGB(*CHAR)                 # logo claro -> pastilha escura
                c.roundRect(bx + (bw - pw) / 2, cy - ph / 2, pw, ph, 6, fill=1, stroke=0)
            else:
                c.setFillColorRGB(*CREAM)                # logo escuro -> pastilha clara
                c.setStrokeColorRGB(*LINE)
                c.setLineWidth(0.4)
                c.roundRect(bx + (bw - pw) / 2, cy - ph / 2, pw, ph, 6, fill=1, stroke=1)
            c.drawImage(ImageReader(AS + p['file']), bx + (bw - lw) / 2, cy - lh / 2,
                        lw, lh, mask='auto')

        if col == 0 and i + 1 < len(ITENS_PARC):
            fio_vertical(c, TX + bw, by - bh + 16, by - 16, LINE, 0.4)
        if row < (len(ITENS_PARC) - 1) // 2:
            fio(c, TX, W - RM, by - bh, LINE, 0.4)
    fecha(c)


    # ============================ PESSOAS ============================
    def pagina_pessoas(kicker, tit, ital, sub, itens, prefixo, cols, ghost_n):
        c.setFillColorRGB(*WHITE)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        ghost(c, ghost_n, W - RM, H - 150)
        y = cabeca(c, kicker, tit, ital)
        y = para(c, sub, TX, y + 10, 'PopL', 9, 14, CW, GREY) - 34
        gap = 18.0
        fw = (CW - gap * (cols - 1)) / cols
        for i, (nome, arroba) in enumerate(itens):
            col, row = i % cols, i // cols
            bx = TX + col * (fw + gap)
            by = y - row * (fw + 62)
            # painel em arco atras da foto
            arco(c, bx, by - fw - 6, fw, fw + 26, SAND)
            c.drawImage(cover(AS + f'{prefixo}{i}.jpg', fw - 16, fw - 16, f'{prefixo}p{i}', focus=0.5),
                        bx + 8, by - fw + 2, fw - 16, fw - 16)
            c.setFont('PopM', 8.8)
            c.setFillColorRGB(*CHAR)
            c.drawString(bx, by - fw - 24, nome)
            c.setFont('PopL', 7.4)
            c.setFillColorRGB(*BRONZE)
            c.drawString(bx, by - fw - 36, arroba)
        fecha(c)


    pagina_pessoas('REDE D’CORATTO', 'Clientes', 'parceiros',
                   'Quem já vive um projeto D’Coratto e assina embaixo.',
                   CLIENTES, 'cliente_', 2, '07')

    # ---------------------------- EMBAIXADOR ----------------------------
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    fh = 430.0
    c.drawImage(cover(AS + 'embaixador.jpg', W, fh, 'emb', focus=0.18), 0, H - fh, W, fh)
    marginalia(c, 'EMBAIXADOR DA MARCA')
    c.setFont('Lora', 27)
    c.setFillColorRGB(*CHAR)
    c.drawString(TX, H - fh - 46, 'Thiago Miranda')
    fio(c, TX, TX + 38, H - fh - 64, BRONZE, 1.1)
    c.setFont('PopL', 8.2)
    c.setFillColorRGB(*BRONZE)
    c.drawString(TX, H - fh - 84, '@thiagomiranda01')
    y = para(c, 'Thiago Miranda é embaixador da D’Coratto. Na foto, ao lado de Wellington Brito, CEO '
                'da marca. A parceria nasce do mesmo princípio que rege cada projeto: quem representa '
                'a D’Coratto precisa, antes de tudo, viver a D’Coratto.',
             TX, H - fh - 112, 'PopL', 9.2, 15.5, CW) - 30

    fio(c, TX, W - RM, y + 8, LINE, 0.5)
    c.setFont('LoraIt', 16)
    c.setFillColorRGB(*CHAR)
    c.drawString(TX, y - 22, 'Mais que móveis, entregamos pertencimento.')
    para(c, 'Cada canto do que entregamos carrega um pedaço da nossa história — e da história de '
            'quem confia na gente.', TX, y - 44, 'PopL', 8.4, 13, CW, GREY)
    fecha(c)

    # ---------------------------- ARQUITETOS ----------------------------
    def grade_arq(c, y):
        """Grade da rede em 5 colunas (foto ~2,6 cm), na mesma pagina do destaque."""
        cols = 5
        gap = 18.0
        fw = (CW - gap * (cols - 1)) / cols
        for i, (nome, arroba, _fimg) in enumerate(ARQUITETOS):
            col, row = i % cols, i // cols
            bx = TX + col * (fw + gap)
            by = y - row * (fw + 52)
            arco(c, bx, by - fw - 6, fw, fw + 20, SAND)
            c.drawImage(cover(AS + _fimg, fw - 16, fw - 16, f'arqp{i}', focus=0.5),
                        bx + 8, by - fw + 2, fw - 16, fw - 16)
            c.setFont('PopM', 7.6)
            c.setFillColorRGB(*CHAR)
            for _j, _ln in enumerate(wrap(nome, 'PopM', 7.6, fw)[:2]):
                c.drawString(bx, by - fw - 20 - _j * 10, _ln)
            # @ longo encolhe ate caber na coluna (ex.: @carolcunha.designinealmeida.ca)
            _fs = 6.4
            while _fs > 4.8 and pdfmetrics.stringWidth(arroba, 'PopL', _fs) > fw:
                _fs -= 0.2
            c.setFont('PopL', _fs)
            c.setFillColorRGB(*BRONZE)
            c.drawString(bx, by - fw - 31 - (10 if len(wrap(nome, 'PopM', 7.6, fw)) > 1 else 0),
                         arroba)
        return y - (-(-len(ARQUITETOS) // cols)) * (fw + 52)


    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '09', W - RM, H - 150)

    _tipo = ARQ.get('tipo', 'nenhum')
    _foto = ARQ.get('foto')
    _destaque = (_tipo == 'novo' and _foto) or _tipo == 'cadastrado'

    if _destaque:
        if SO_ESTE_ARQ:
            y = cabeca(c, 'REDE D’CORATTO', 'Arquiteto', 'do projeto')
            y = para(c, 'O profissional que assina este projeto.',
                     TX, y + 10, 'PopL', 9, 14, CW, GREY) - 26
        else:
            y = cabeca(c, 'REDE D’CORATTO', 'Arquitetos', 'e engenheiros')
            y = para(c, 'Profissionais que especificam D’Coratto nos seus projetos.',
                     TX, y + 10, 'PopL', 9, 14, CW, GREY) - 26

        # --- destaque: arquiteto do projeto ---
        _nome = ARQ.get('nome') or 'Arquiteto'
        _insta = ARQ.get('insta') or ''
        _primeiro = _nome.replace('Arquiteto', '').replace('Arquiteta', '').strip().split(' ')[0]
        _fpath = _foto if _tipo == 'novo' else (AS + 'arq_diego.jpg')

        if SO_ESTE_ARQ:
            # Sozinho na pagina: foto grande em cima e texto embaixo, em largura
            # cheia. Tentei foto grande com texto AO LADO e a coluna sobrou com
            # 136pt — o kicker ja estourava a margem.
            fw2 = 320.0
            fh2 = 330.0
            fx2 = TX + (CW - fw2) / 2.0
            arco(c, fx2, y - fh2 - 6, fw2, fh2 + 24, SAND)
            c.drawImage(cover(_fpath, fw2 - 14, fh2 - 14, 'arqdest', focus=0.38),
                        fx2 + 7, y - fh2 + 1, fw2 - 14, fh2 - 14)
            y = y - fh2 - 34
            tracked(c, 'ARQUITETO DO PROJETO', TX, y, 'PopM', 7, 2.8, BRONZE)
            y -= 30
            _ln, _tn = _ajusta_titulo(_nome, 'Lora', 28, CW)
            c.setFont('Lora', _tn)
            c.setFillColorRGB(*CHAR)
            for _i, _l in enumerate(_ln):
                c.drawString(TX, y - _i * (_tn * 1.16), _l)
            y -= (len(_ln) - 1) * (_tn * 1.16)
            if _insta:
                c.setFont('PopL', 10)
                c.setFillColorRGB(*BRONZE)
                c.drawString(TX, y - 20, _insta)
                y -= 20
            fio(c, TX, W - RM, y - 18, LINE, 0.6)
            y = para(c, 'A assinatura por trás deste projeto. É da visão de ' + _primeiro +
                        ' que nasce cada ambiente desta proposta: a leitura do espaço, a escolha '
                        'dos materiais e a proporção de cada peça. A D’Coratto executa o que foi '
                        'desenhado, com marmoraria própria e acabamentos especiais — para que o '
                        'projeto chegue à obra exatamente como foi concebido.',
                     TX, y - 40, 'PopL', 9.2, 15, CW, MID) - 18
            c.setFont('LoraIt', 15)
            c.setFillColorRGB(*CHAR)
            c.drawString(TX, y, 'Projeto e execução, na mesma direção.')
        else:
            dh = 128.0
            dw = dh * 594 / 616
            arco(c, TX, y - dh - 6, dw, dh + 22, SAND)
            c.drawImage(cover(_fpath, dw - 12, dh - 12, 'diego', focus=0.4),
                        TX + 6, y - dh + 0, dw - 12, dh - 12)
            tx2 = TX + dw + 24
            tracked(c, 'ARQUITETO DO PROJETO', tx2, y - 16, 'PopM', 7, 2.8, BRONZE)
            c.setFont('Lora', 22)
            c.setFillColorRGB(*CHAR)
            c.drawString(tx2, y - 44, _nome)
            if _insta:
                c.setFont('PopL', 9)
                c.setFillColorRGB(*BRONZE)
                c.drawString(tx2, y - 61, _insta)
            # frase sem genero: a lista tem homens e mulheres, e antes saia
            # "do arquiteto Karin", "do arquiteto Luana"...
            para(c, 'A assinatura por trás deste projeto. É da visão de ' + _primeiro +
                    ' que nasce cada ambiente desta proposta — e é com profissionais assim '
                    'que a D’Coratto constrói seus melhores trabalhos.',
                 tx2, y - 84, 'PopL', 8.4, 13, W - RM - tx2, MID)

        if not SO_ESTE_ARQ:
            fio(c, TX, W - RM, y - dh - 22, LINE, 0.5)
            y = y - dh - 52
            # a rede completa entra na MESMA pagina, logo abaixo do destaque
            grade_arq(c, y)
        fecha(c)
    else:
        # sem arquiteto do projeto: rede completa em grade de 3, sem destaque
        y = cabeca(c, 'REDE D’CORATTO', 'Arquitetos', 'e engenheiros')
        y = para(c, 'Profissionais que especificam D’Coratto nos seus projetos.',
                 TX, y + 10, 'PopL', 9, 14, CW, GREY) - 30
        grade_arq(c, y)
        fecha(c)

    # ============================ ENCERRAMENTO ============================
    c.drawImage(cover(_fundo, W, H, 'fim', focus=0.45, darken=0.36), 0, 0, W, H)
    for i in range(50):
        t = i / 49.0
        c.setFillColorRGB(CHAR[0], CHAR[1], CHAR[2], alpha=t * 0.55)
        c.rect(0, i * 6, W, 7, fill=1, stroke=0)
    c.drawImage(ImageReader(AS + 'logo.png'), W / 2 - 88, H - 236, 176, 86, mask='auto')
    c.setFont('Lora', 24)
    c.setFillColorRGB(*WHITE)
    c.drawCentredString(W / 2, 430, 'Sonhos são únicos.')
    c.setFont('LoraIt', 24)
    c.setFillColorRGB(0.85, 0.72, 0.55)
    c.drawCentredString(W / 2, 394, 'Os detalhes fazem a diferença.')
    fio(c, W / 2 - 26, W / 2 + 26, 370, BRONZE, 1.1)
    c.setFont('PopL', 8.4)
    c.setFillColorRGB(0.86, 0.86, 0.87)
    c.drawCentredString(W / 2, 300, 'Estrada da Pedreira, 554 – Parquelândia, Mogi das Cruzes/SP – 08771-210')
    c.drawCentredString(W / 2, 282, 'Showroom  ·  Marmoraria própria  ·  Atendimento em todo o território nacional')
    c.showPage()

    c.save()
    return PAG[0] + 1
