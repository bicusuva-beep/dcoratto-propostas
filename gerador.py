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
    PRAZO = dados.get('prazo') or ''
    CONTATO = ''

    AMBIENTES = []
    for i, a in enumerate(dados['ambientes']):
        num = f'{i + 1:02d}'
        AMBIENTES.append((num, a['nome'], float(a['valor']),
                          (float(a['parcela']) if a.get('parcela') else None),
                          a.get('desc', ''), list(a.get('fotos', []))))
    TOTAL = sum(a[2] for a in AMBIENTES)
    _parcs = [a[3] for a in AMBIENTES]
    TOTAL_PARC = sum(_parcs) if (_parcs and all(p for p in _parcs)) else None

    ARQ = dados.get('arquiteto') or {'tipo': 'nenhum'}

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
    ARQUITETOS = [('Tamyres Marques', '@tamyarquiteta'), ('Jornate Obras', '@jornateobras'),
                  ('Eng. Kethelyn', '@legus.engenharia'), ('Bianca Jurtick', '@aconstrutora.br'),
                  ('Carol Cunha', '@carolcunha.designinealmeida.ca')]
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


    def cabeca(c, kicker, titulo, italico=None, y=H - 118):
        """Titulo editorial: numeral fantasma + titulo + fio curto."""
        marginalia(c, kicker)
        c.setFont('Lora', 27)
        c.setFillColorRGB(*CHAR)
        c.drawString(TX, y, titulo)
        if italico:
            c.setFont('LoraIt', 27)
            c.setFillColorRGB(*BRONZE)
            c.drawString(TX, y - 32, italico)
            y -= 32
        fio(c, TX, TX + 38, y - 18, BRONZE, 1.1)
        return y - 48


    def arco(c, x, y, w, h, cor=CREAM):
        """Painel em arco (topo semicircular) usado como fundo — nunca corta imagem."""
        r = w / 2.0
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
    y = 300
    for n, nome, val, _, _, _ in AMBIENTES:
        c.setFont('Lora', 19)
        c.setFillColorRGB(0.85, 0.72, 0.55)
        c.drawString(TX, y, n)
        c.setFont('PopL', 14)
        c.setFillColorRGB(*WHITE)
        c.drawString(TX + 42, y, nome)
        fio(c, TX, W - RM, y - 16, (0.5, 0.5, 0.52), 0.6)
        y -= 46
    fecha(c, escuro=True)

    # ============================ AMBIENTES ============================
    def render_h(c, path, x, y, boxw, boxh, key):
        """Render horizontal completo, sem recorte, sobre painel em arco."""
        f, w, h = contain(path, boxw, boxh, key)
        ix = x + (boxw - w) / 2
        iy = y + (boxh - h) / 2
        arco(c, ix - 13, iy - 12, w + 26, h + 30)
        c.drawImage(f, ix, iy, w, h)
        fio(c, ix, ix + w, iy - 6, LINE, 0.5)
        return w, h


    for n, nome, val, parc, desc, fotos in AMBIENTES:
        c.setFillColorRGB(*WHITE)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        ghost(c, n, W - RM, H - 152)
        y = cabeca(c, 'AMBIENTE ' + n, nome)
        y = para(c, desc, TX, y + 10, 'PopL', 9.2, 15.5, CW) - 26

        if not fotos:
            y = y - 20
        elif len(fotos) == 1:
            render_h(c, fotos[0], TX, y - 300, CW, 300, f'r{n}_0')
            y = y - 300 - 32
        else:
            bh = 214.0
            gap = 14.0
            render_h(c, fotos[0], TX, y - bh, CW, bh, f'r{n}_0')
            render_h(c, fotos[1], TX, y - 2 * bh - gap, CW, bh, f'r{n}_1')
            y = y - 2 * bh - gap - 28

        fio(c, TX, W - RM, y + 4, LINE, 0.5)
        tracked(c, 'INVESTIMENTO DO AMBIENTE', TX, y - 22, 'PopM', 7, 3, BRONZE)
        c.setFont('Lora', 24)
        c.setFillColorRGB(*CHAR)
        c.drawRightString(W - RM, y - 26, brl(val))
        if parc:
            c.setFont('PopL', 8)
            c.setFillColorRGB(*GREY)
            c.drawRightString(W - RM, y - 42, f'ou 12x de {brl(parc)}')
        fecha(c)

    # ============================ INVESTIMENTO ============================
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '$', W - RM, H - 150)
    y = cabeca(c, 'RESUMO', 'Investimento')
    c.setFont('PopM', 7)
    c.setFillColorRGB(*GREY)
    c.drawString(TX, y + 16, 'AMBIENTE')
    c.drawRightString(W - RM, y + 16, 'VALOR')
    fio(c, TX, W - RM, y + 6, CHAR, 0.8)
    y -= 18
    for n, nome, val, parc, desc, fotos in AMBIENTES:
        c.setFont('Lora', 30)
        c.setFillColorRGB(*SAND)
        c.drawString(TX - 42, y - 8, n)
        c.setFont('PopM', 12.5)
        c.setFillColorRGB(*CHAR)
        c.drawString(TX, y, nome)
        c.setFont('Lora', 16)
        c.setFillColorRGB(*CHAR)
        c.drawRightString(W - RM, y, brl(val))
        if parc:
            c.setFont('PopL', 7.6)
            c.setFillColorRGB(*BRONZE)
            c.drawRightString(W - RM, y - 14, f'ou 12x de {brl(parc)}')
        yy = para(c, desc, TX, y - 20, 'PopL', 8.2, 12.5, CW - 150, GREY)
        fio(c, TX, W - RM, yy - 8, LINE, 0.5)
        y = yy - 34

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
        c.drawRightString(W - RM, y - 68, f'ou 12x de {brl(TOTAL_PARC)}')

    y -= 132
    c.setFont('PopM', 8.6)
    c.setFillColorRGB(*CHAR)
    c.drawString(TX, y, 'Validade da proposta')
    c.setFont('PopL', 8.6)
    c.setFillColorRGB(*MID)
    c.drawString(TX + 132, y, VALIDADE)
    fio(c, TX, W - RM, y - 10, LINE, 0.4)
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
    arco(c, TX, y - 152, CW, 152, CREAM)
    c.setFont('LoraIt', 15)
    c.setFillColorRGB(*CHAR)
    c.drawCentredString(TX + CW / 2, y - 52, 'Cuidados com a sua obra')
    para(c, 'Respeitamos o seu investimento. Toda etapa da obra é acompanhada pelo nosso líder de '
            'pós-venda, e existe a preparação de todo o ambiente para receber o material — para que '
            'seja uma obra limpa e tranquila.',
         TX + 44, y - 78, 'PopL', 8.4, 13, CW - 88)
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
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    ghost(c, '09', W - RM, H - 150)

    _tipo = ARQ.get('tipo', 'nenhum')
    _foto = ARQ.get('foto')
    _destaque = (_tipo == 'novo' and _foto) or _tipo == 'cadastrado'

    if _destaque:
        y = cabeca(c, 'REDE D’CORATTO', 'Arquitetos', 'e engenheiros')
        y = para(c, 'Profissionais que especificam D’Coratto nos seus projetos.',
                 TX, y + 10, 'PopL', 9, 14, CW, GREY) - 26

        # --- destaque: arquiteto do projeto ---
        dh = 128.0
        dw = dh * 594 / 616
        _nome = ARQ.get('nome') or 'Arquiteto'
        _insta = ARQ.get('insta') or ''
        _primeiro = _nome.replace('Arquiteto', '').replace('Arquiteta', '').strip().split(' ')[0]
        _fpath = _foto if _tipo == 'novo' else (AS + 'arq_diego.jpg')
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
        para(c, 'A assinatura por trás deste projeto. É da visão do arquiteto ' + _primeiro +
                ' que nasce cada ambiente desta proposta — e é com profissionais assim que a '
                'D’Coratto constrói seus melhores trabalhos.',
             tx2, y - 84, 'PopL', 8.4, 13, W - RM - tx2, MID)
        fio(c, TX, W - RM, y - dh - 22, LINE, 0.5)
        y = y - dh - 44

        cols = 3
        gap = 18.0
        fw = (CW - gap * (cols - 1)) / cols
        for i, (nome, arroba) in enumerate(ARQUITETOS):
            col, row = i % cols, i // cols
            bx = TX + col * (fw + gap)
            by = y - row * (fw + 52)
            arco(c, bx, by - fw - 6, fw, fw + 20, SAND)
            c.drawImage(cover(AS + f'arq_{i}.jpg', fw - 16, fw - 16, f'arqp{i}', focus=0.5),
                        bx + 8, by - fw + 2, fw - 16, fw - 16)
            c.setFont('PopM', 8.4)
            c.setFillColorRGB(*CHAR)
            c.drawString(bx, by - fw - 20, nome)
            c.setFont('PopL', 7.2)
            c.setFillColorRGB(*BRONZE)
            c.drawString(bx, by - fw - 31, arroba)
        fecha(c)
    else:
        # sem arquiteto do projeto: rede completa em grade de 3, sem destaque
        y = cabeca(c, 'REDE D’CORATTO', 'Arquitetos', 'e engenheiros')
        y = para(c, 'Profissionais que especificam D’Coratto nos seus projetos.',
                 TX, y + 10, 'PopL', 9, 14, CW, GREY) - 30
        cols = 3
        gap = 18.0
        fw = (CW - gap * (cols - 1)) / cols
        for i, (nome, arroba) in enumerate(ARQUITETOS):
            col, row = i % cols, i // cols
            bx = TX + col * (fw + gap)
            by = y - row * (fw + 60)
            arco(c, bx, by - fw - 6, fw, fw + 22, SAND)
            c.drawImage(cover(AS + f'arq_{i}.jpg', fw - 16, fw - 16, f'arqp{i}', focus=0.5),
                        bx + 8, by - fw + 2, fw - 16, fw - 16)
            c.setFont('PopM', 8.6)
            c.setFillColorRGB(*CHAR)
            c.drawString(bx, by - fw - 22, nome)
            c.setFont('PopL', 7.2)
            c.setFillColorRGB(*BRONZE)
            c.drawString(bx, by - fw - 34, arroba)
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
