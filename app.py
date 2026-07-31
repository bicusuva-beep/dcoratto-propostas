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

st.set_page_config(page_title="D'Coratto · Gerador de Propostas",
                   page_icon="📄", layout="centered")

# ------------------------------------------------------------------ estilo
st.markdown("""
<style>
  .stApp { background:#F4F1EC; }
  /* Garante contraste mesmo se o navegador estiver em modo escuro. */
  .stApp, .stApp p, .stApp span, .stApp div, .stApp label,
  .stMarkdown, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * ,
  .stRadio label, .stCaption, [data-testid="stCaptionContainer"],
  [data-testid="stFileUploaderDropzone"] { color:#35363A !important; }
  .stTextInput input, .stTextArea textarea, .stNumberInput input {
      background:#FFFFFF !important; color:#35363A !important;
      border:1px solid #D8D2C7 !important; }
  .stSelectbox div[data-baseweb="select"] > div {
      background:#FFFFFF !important; color:#35363A !important; }
  [data-testid="stFileUploaderDropzone"] { background:#FFFFFF !important; }
  [data-testid="stNotification"] * { color:inherit !important; }
  h1, h2, h3 { color:#35363A; font-family:Georgia, serif; }
  .dco-title { font-family:Georgia,serif; font-size:30px; color:#35363A; margin-bottom:0; }
  .dco-title i { color:#A7723B; }
  .dco-sub { color:#737378; font-size:14px; margin-top:2px; margin-bottom:18px; }
  .dco-kicker { color:#A7723B; letter-spacing:2.5px; font-size:12px; text-transform:uppercase;
                font-weight:600; margin:22px 0 6px; }
  .stButton>button { background:#35363A; color:#fff; border:none; border-radius:8px;
                     padding:10px 20px; font-weight:500; }
  .stButton>button:hover { background:#26272b; color:#fff; }
  .stDownloadButton>button { background:#A7723B; color:#fff; border:none; border-radius:8px;
                             padding:12px 22px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ acesso
# A senha e lida de st.secrets["APP_SENHA"]. Se nao estiver configurada,
# o app abre normalmente (uso local). Em producao, SEMPRE configure a senha.
_SENHA = st.secrets.get("APP_SENHA", "") if hasattr(st, "secrets") else ""
if _SENHA:
    if not st.session_state.get("_ok"):
        st.markdown('<div class="dco-title">Gerador de <i>Propostas</i></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="dco-sub">Acesso restrito à equipe D\'Coratto.</div>',
                    unsafe_allow_html=True)
        _t = st.text_input("Senha de acesso", type="password")
        if st.button("Entrar"):
            if _t == _SENHA:
                st.session_state["_ok"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        st.stop()

st.markdown('<div class="dco-title">Gerador de <i>Propostas</i></div>', unsafe_allow_html=True)
st.markdown('<div class="dco-sub">Preencha os campos, adicione as fotos de cada ambiente e '
            'gere o PDF no formato aprovado. A data entra automática no dia da geração.</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------ estado
if "n_amb" not in st.session_state:
    st.session_state.n_amb = 1

# ------------------------------------------------------------------ dados do projeto
st.markdown('<div class="dco-kicker">Dados do projeto</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
cliente = c1.text_input("Cliente", placeholder="Nome do cliente")
proposta = c2.text_input("Nº da proposta (opcional)", placeholder="ex.: 2026-014")
c3, c4 = st.columns(2)
validade = c3.text_input("Validade da proposta", value="10 dias")
pagamento = c4.text_input("Forma de pagamento (opcional)",
                          placeholder="ex.: 40% entrada + 12x no cartão")

# ------------------------------------------------------------------ ambientes
st.markdown('<div class="dco-kicker">Ambientes</div>', unsafe_allow_html=True)

cadd, cdel = st.columns([1, 1])
if cadd.button("➕ Adicionar ambiente"):
    st.session_state.n_amb += 1
if cdel.button("➖ Remover último") and st.session_state.n_amb > 1:
    st.session_state.n_amb -= 1

ambientes = []
for i in range(st.session_state.n_amb):
    with st.container(border=True):
        st.markdown(f"**Ambiente {i + 1:02d}**")
        nome = st.text_input("Nome do ambiente", key=f"nome{i}",
                             placeholder="ex.: Cozinha, Cristaleira, Closet...")
        desc = st.text_area("Descrição", key=f"desc{i}", height=90,
                            placeholder="Materiais, acabamentos, iluminação, ferragens...")
        v1, v2 = st.columns(2)
        valor = v1.number_input("Valor à vista (R$)", key=f"valor{i}",
                                min_value=0.0, step=100.0, format="%.2f")
        parcela = v2.number_input("Valor da parcela 12x (R$) — opcional", key=f"parc{i}",
                                  min_value=0.0, step=10.0, format="%.2f")
        fotos = st.file_uploader("Fotos (1 = página inteira · 2 = empilhadas)",
                                 key=f"fotos{i}", type=["jpg", "jpeg", "png"],
                                 accept_multiple_files=True)
        ambientes.append({"nome": nome, "desc": desc, "valor": valor,
                          "parcela": parcela if parcela > 0 else None,
                          "fotos_raw": fotos[:2] if fotos else []})

# total ao vivo
_total = sum(a["valor"] for a in ambientes if a["valor"])
st.markdown(f"<div style='text-align:right; font-family:Georgia,serif; font-size:22px; "
            f"color:#35363A;'>Total: R$ {_total:,.2f}</div>".replace(",", "X")
            .replace(".", ",").replace("X", "."), unsafe_allow_html=True)

# ------------------------------------------------------------------ arquiteto
st.markdown('<div class="dco-kicker">Arquiteto do projeto</div>', unsafe_allow_html=True)
_opcoes = ["Sem arquiteto parceiro"]
if ARQ_SALVOS:
    _opcoes.append("Escolher da lista")
_opcoes.append("Cadastrar novo")

modo = st.radio("", _opcoes, horizontal=True, label_visibility="collapsed")

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
def _br(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

if st.button("Gerar proposta em PDF", type="primary"):
    erros = []
    if not cliente.strip():
        erros.append("Informe o nome do cliente.")
    for i, a in enumerate(ambientes):
        if not a["nome"].strip():
            erros.append(f"Ambiente {i + 1:02d} está sem nome.")
        if not a["valor"] or a["valor"] <= 0:
            erros.append(f"Ambiente {i + 1:02d} está sem valor.")
    if erros:
        for e in erros:
            st.error(e)
    else:
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
