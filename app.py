# -*- coding: utf-8 -*-
"""
D'Coratto — Gerador de Propostas (Streamlit)
Usa o mesmo motor ReportLab do PDF aprovado (gerador.py), garantindo saida identica.
"""
import json
import os
import tempfile
from datetime import date

import streamlit as st
import gerador

_BASE = os.path.dirname(os.path.abspath(__file__))


def _dir_assets():
    """Aceita os dois layouts: pasta assets/ ou tudo na raiz."""
    a = os.path.join(_BASE, "assets")
    return a if os.path.isdir(a) else _BASE


def _carrega_arquitetos():
    for base in (_BASE, _dir_assets()):
        f = os.path.join(base, "arquitetos.json")
        if os.path.exists(f):
            try:
                with open(f, encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return []
    return []


ARQ_SALVOS = _carrega_arquitetos()


def _br(v):
    """Formata numero no padrao brasileiro: 46489.81 -> 46.489,81"""
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="D'Coratto · Gerador de Propostas",
                   page_icon="📄", layout="centered")

# ------------------------------------------------------------------ estilo
st.markdown("""
<style>
  /* O tema (fundo, cor de texto, tema claro fixo) vem de .streamlit/config.toml.
     Aqui ficam SO os detalhes de marca. Nao usar seletores genericos com
     !important: eles atingem o texto dentro dos botoes e o deixam invisivel. */
  h1, h2, h3 { color:#35363A; font-family:Georgia, serif; }
  .dco-title { font-family:Georgia,serif; font-size:30px; color:#35363A; margin-bottom:0; }
  .dco-title i { color:#A7723B; }
  .dco-sub { color:#737378; font-size:14px; margin-top:2px; margin-bottom:18px; }
  .dco-kicker { color:#A7723B; letter-spacing:2.5px; font-size:12px; text-transform:uppercase;
                font-weight:600; margin:22px 0 6px; }
  .dco-total { text-align:right; font-family:Georgia,serif; font-size:22px; color:#35363A; }
  .stButton>button { background:#35363A; color:#fff; border:none; border-radius:8px;
                     padding:10px 20px; font-weight:500; }
  .stButton>button:hover { background:#26272b; color:#fff; }
  .stDownloadButton>button { background:#A7723B; color:#fff; border:none; border-radius:8px;
                             padding:12px 22px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dco-title">Gerador de <i>Propostas</i></div>', unsafe_allow_html=True)
st.markdown('<div class="dco-sub">Preencha os campos, adicione as fotos de cada ambiente e '
            'gere o PDF no formato aprovado. A data entra automática no dia da geração.</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------ estado
# 'slots' guarda IDs estaveis dos ambientes. A ORDEM da lista e a ordem que sai
# no PDF. Reordenar = trocar posicoes nesta lista; os campos nao sao tocados,
# porque cada widget usa a key do seu slot, nao a posicao.
if "slots" not in st.session_state:
    st.session_state.slots = [0]
    st.session_state.prox_id = 1

# reordenacao pendente, aplicada ANTES dos widgets existirem
if "_mover" in st.session_state:
    _a, _b = st.session_state.pop("_mover")
    _s = st.session_state.slots
    _s[_a], _s[_b] = _s[_b], _s[_a]

# ------------------------------------------------------------------ dados do projeto
st.markdown('<div class="dco-kicker">Dados do projeto</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
cliente = c1.text_input("Cliente", placeholder="Nome do cliente")
proposta = c2.text_input("Nº da proposta (opcional)", placeholder="ex.: 2026-014")
c3, c4 = st.columns(2)
validade = c3.text_input("Validade da proposta", value="10 dias")
pagamento = c4.text_input("Forma de pagamento (opcional)",
                          placeholder="ex.: 40% entrada + 12x no cartão")
n_parcelas = st.number_input("Parcelar em até quantas vezes", min_value=1, max_value=48,
                             value=12, step=1,
                             help="Usado nas linhas 'ou Nx de R$ ...' do PDF.")

# ------------------------------------------------------------------ ambientes
st.markdown('<div class="dco-kicker">Ambientes</div>', unsafe_allow_html=True)

cadd, cdel = st.columns([1, 1])
if cadd.button("➕ Adicionar ambiente"):
    st.session_state.slots.append(st.session_state.prox_id)
    st.session_state.prox_id += 1
if cdel.button("➖ Remover último") and len(st.session_state.slots) > 1:
    _sid = st.session_state.slots.pop()
    for _k in (f"nome{_sid}", f"desc{_sid}", f"valor{_sid}", f"parc{_sid}", f"fotos{_sid}"):
        st.session_state.pop(_k, None)

st.caption("Use ▲ ▼ para mudar a ordem em que os ambientes aparecem no PDF.")

ambientes = []
_total_slots = len(st.session_state.slots)
for pos, sid in enumerate(st.session_state.slots):
    with st.container(border=True):
        hcab, hsobe, hdesce = st.columns([6, 1, 1])
        hcab.markdown(f"**Ambiente {pos + 1:02d}**")
        if hsobe.button("▲", key=f"up{sid}", disabled=(pos == 0),
                        help="Subir este ambiente"):
            st.session_state["_mover"] = (pos, pos - 1)
            st.rerun()
        if hdesce.button("▼", key=f"dn{sid}", disabled=(pos == _total_slots - 1),
                         help="Descer este ambiente"):
            st.session_state["_mover"] = (pos, pos + 1)
            st.rerun()
        nome = st.text_input("Nome do ambiente", key=f"nome{sid}",
                             placeholder="ex.: Cozinha, Cristaleira, Closet...")
        desc = st.text_area("Descrição", key=f"desc{sid}", height=90,
                            placeholder="Materiais, acabamentos, iluminação, ferragens...")
        v1, v2 = st.columns(2)
        valor = v1.number_input("Valor à vista (R$)", key=f"valor{sid}",
                                min_value=0.0, step=100.0, format="%.2f")
        parcela = v2.number_input(f"Valor da parcela {n_parcelas}x (R$) — opcional",
                                  key=f"parc{sid}",
                                  min_value=0.0, step=10.0, format="%.2f")
        fotos = st.file_uploader("Fotos do ambiente (1 a 4 — todas entram na página do ambiente)",
                                 key=f"fotos{sid}", type=["jpg", "jpeg", "png"],
                                 accept_multiple_files=True)
        ambientes.append({"nome": nome, "desc": desc, "valor": valor,
                          "parcela": parcela if parcela > 0 else None,
                          "fotos_raw": fotos[:4] if fotos else []})

# total ao vivo
_total = sum(a["valor"] for a in ambientes if a["valor"])
st.markdown(f'<div class="dco-total">Total: R$ {_br(_total)}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ arquiteto
st.markdown('<div class="dco-kicker">Arquiteto do projeto</div>', unsafe_allow_html=True)
_opcoes = ["Sem arquiteto parceiro"]
if ARQ_SALVOS:
    _opcoes.append("Escolher da lista")
_opcoes.append("Cadastrar novo")

modo = st.radio("Arquiteto", _opcoes, horizontal=True, label_visibility="collapsed")

arq = {"tipo": "nenhum"}

if modo == "Escolher da lista":
    _nomes = [a["nome"] for a in ARQ_SALVOS]
    _sel = st.selectbox("Arquiteto do projeto", _nomes)
    _reg = next(a for a in ARQ_SALVOS if a["nome"] == _sel)
    _fp = os.path.join(_dir_assets(), _reg.get("foto", ""))
    if not os.path.exists(_fp):
        _fp = None
    c_a, c_b = st.columns([1, 3])
    if _fp:
        c_a.image(_fp, width=110)
    else:
        c_a.warning("Sem foto")
    c_b.markdown(f"**{_reg['nome']}**")
    c_b.caption(_reg.get("insta", "") or "sem @")
    arq = {"tipo": "novo", "nome": _reg["nome"],
           "insta": _reg.get("insta", ""), "foto_path": _fp}
    st.caption("O arquiteto aparece com destaque como autor do projeto.")

elif modo == "Cadastrar novo":
    a1, a2 = st.columns(2)
    arq_nome = a1.text_input("Nome do arquiteto", placeholder="ex.: Arquiteto Diego")
    arq_insta = a2.text_input("Instagram", placeholder="@exemplararquitetura")
    arq_foto = st.file_uploader("Foto do arquiteto", type=["jpg", "jpeg", "png"], key="arqfoto")
    arq = {"tipo": "novo", "nome": arq_nome, "insta": arq_insta, "foto_raw": arq_foto}
    st.caption("O arquiteto aparece com destaque como autor do projeto.")
    if arq_nome.strip():
        with st.expander("Para este arquiteto aparecer na lista nas próximas vezes"):
            st.write("O app não guarda cadastro sozinho (o servidor reinicia e apaga). "
                     "Para fixar, faça 2 coisas no GitHub:")
            st.write("**1.** Suba a foto dele com um nome novo, ex.: `arq_novo1.jpg`")
            st.write("**2.** Edite o `arquitetos.json` e acrescente esta linha:")
            st.code(json.dumps({"nome": arq_nome.strip(),
                                "insta": arq_insta.strip(),
                                "foto": "arq_novo1.jpg"}, ensure_ascii=False),
                    language="json")
else:
    st.caption("A página de arquitetos aparece sem destaque, só com a rede de parceiros.")

st.divider()

# ------------------------------------------------------------------ gerar
def _valida():
    """Devolve (erros, avisos) sem gerar nada."""
    er, av = [], []
    if not cliente.strip():
        er.append("Informe o nome do cliente.")
    for k, a in enumerate(ambientes):
        if not a["nome"].strip():
            er.append(f"Ambiente {k + 1:02d} está sem nome.")
        if not a["valor"] or a["valor"] <= 0:
            er.append(f"Ambiente {k + 1:02d} está sem valor.")
        if not a["fotos_raw"]:
            av.append(f"Ambiente {k + 1:02d} está sem foto — a página sai só com texto e valor.")
        elif len(st.session_state.get(f"fotos{st.session_state.slots[k]}") or []) > 4:
            av.append(f"Ambiente {k + 1:02d}: só as 4 primeiras fotos entram no PDF. "
                      f"As demais são ignoradas.")
        if not a["desc"].strip():
            av.append(f"Ambiente {k + 1:02d} está sem descrição.")
        if not a["parcela"]:
            av.append(f"Ambiente {k + 1:02d} está sem valor de parcela — a linha "
                      f"'ou {n_parcelas}x de ...' não aparece.")
    if not pagamento.strip():
        av.append("Forma de pagamento em branco — não aparece no PDF.")
    elif len(pagamento.strip()) > 170:
        av.append(f"Forma de pagamento com {len(pagamento.strip())} caracteres. "
                  f"No PDF cabem cerca de 170 (3 linhas) — o excedente é cortado. "
                  f"Encurte o texto.")
    return er, av


# ------------------------------------------------------------------ conferir
if st.button("👁 Conferir antes de gerar"):
    st.session_state["_ver"] = True

if st.session_state.get("_ver"):
    _er, _av = _valida()
    st.markdown('<div class="dco-kicker">Conferência</div>', unsafe_allow_html=True)
    for _e in _er:
        st.error(_e)
    for _a in _av:
        st.warning(_a)
    if not _er and not _av:
        st.success("Nada pendente.")

    with st.container(border=True):
        st.markdown(f"**Cliente:** {cliente.strip() or '— em branco —'}")
        st.markdown(f"**Nº da proposta:** {proposta.strip() or '— em branco —'}")
        st.markdown(f"**Data no PDF:** {date.today().strftime('%d/%m/%Y')}")
        st.markdown(f"**Validade:** {validade.strip() or '10 dias'}")
        st.markdown(f"**Forma de pagamento:** {pagamento.strip() or '— não sai no PDF —'}")
        _arqtxt = arq.get("nome", "").strip() if arq["tipo"] == "novo" else ""
        st.markdown(f"**Arquiteto em destaque:** {_arqtxt or '— nenhum —'}")

    _tp = 0.0
    for k, a in enumerate(ambientes):
        with st.container(border=True):
            st.markdown(f"**Página do ambiente {k + 1:02d} — "
                        f"{a['nome'].strip() or '(sem nome)'}**")
            st.write(a["desc"].strip() or "_(sem descrição)_")
            cv1, cv2 = st.columns(2)
            cv1.markdown(f"À vista: **R$ {_br(a['valor'] or 0)}**")
            if a["parcela"]:
                cv2.markdown(f"ou **{n_parcelas}x de R$ {_br(a['parcela'])}**")
                _tp += a["parcela"]
            else:
                cv2.markdown("_sem parcelamento_")
            if a["fotos_raw"]:
                st.image([f for f in a["fotos_raw"]], width=190)
            else:
                st.caption("Sem foto.")
    st.markdown(f'<div class="dco-total">Total: R$ {_br(_total)}</div>',
                unsafe_allow_html=True)
    if _tp and all(a["parcela"] for a in ambientes):
        st.markdown(f'<div class="dco-total">ou {n_parcelas}x de R$ {_br(_tp)}</div>',
                    unsafe_allow_html=True)
    else:
        st.caption(f"A linha 'ou {n_parcelas}x de ...' do total só aparece no PDF se "
                   f"TODOS os ambientes tiverem valor de parcela.")
    st.divider()

if st.button("Gerar proposta em PDF", type="primary"):
    erros = []
    if not cliente.strip():
        erros.append("Informe o nome do cliente.")
    for i, a in enumerate(ambientes):
        if not a["nome"].strip():
            erros.append(f"Ambiente {i + 1:02d} está sem nome.")
        if not a["valor"] or a["valor"] <= 0:
            erros.append(f"Ambiente {i + 1:02d} está sem valor.")
    _sem_foto = [f"{i + 1:02d}" for i, a in enumerate(ambientes) if not a["fotos_raw"]]
    if erros:
        for e in erros:
            st.error(e)
    else:
        if _sem_foto:
            st.warning("Sem foto no(s) ambiente(s) " + ", ".join(_sem_foto)
                       + ". A página sai só com o texto e o valor.")
        if len(pagamento.strip()) > 170:
            st.warning(f"A forma de pagamento tem {len(pagamento.strip())} caracteres; "
                       f"no PDF cabem cerca de 170. O texto foi cortado.")
        with st.spinner("Gerando o PDF…"):
            tmp = tempfile.mkdtemp()
            os.environ["DCO_TMP"] = os.path.join(tmp, "_render")

            # salva uploads em disco para o gerador ler
            amb_final = []
            for i, a in enumerate(ambientes):
                paths = []
                for j, f in enumerate(a["fotos_raw"]):
                    p = os.path.join(tmp, f"amb{i}_{j}.jpg")
                    with open(p, "wb") as out:
                        out.write(f.getbuffer())
                    paths.append(p)
                amb_final.append({"nome": a["nome"], "desc": a["desc"],
                                  "valor": a["valor"], "parcela": a["parcela"],
                                  "fotos": paths})

            arq_final = {"tipo": "nenhum"}
            if arq["tipo"] == "novo":
                foto_path = arq.get("foto_path")
                if arq.get("foto_raw"):
                    foto_path = os.path.join(tmp, "arq.jpg")
                    with open(foto_path, "wb") as out:
                        out.write(arq["foto_raw"].getbuffer())
                if arq.get("nome") or foto_path:
                    arq_final = {"tipo": "novo", "nome": arq.get("nome", ""),
                                 "insta": arq.get("insta", ""), "foto": foto_path}

            dados = {
                "cliente": cliente.strip(),
                "proposta": proposta.strip(),
                "data": date.today().strftime("%d/%m/%Y"),
                "validade": validade.strip() or "10 dias",
                "pagamento": pagamento.strip(),
                "parcelas": int(n_parcelas),
                "ambientes": amb_final,
                "arquiteto": arq_final,
            }

            saida = os.path.join(tmp, "proposta.pdf")
            gerador.gerar(dados, saida)
            with open(saida, "rb") as f:
                pdf_bytes = f.read()

        st.success("Proposta gerada.")
        nome_arq = "Proposta " + "".join(ch for ch in cliente if ch.isalnum() or ch in " -").strip() + ".pdf"
        st.download_button("⬇ Baixar PDF", data=pdf_bytes, file_name=nome_arq,
                           mime="application/pdf")
