# -*- coding: utf-8 -*-
"""
D'Coratto — Gerador de Propostas (Streamlit)
Usa o mesmo motor ReportLab do PDF aprovado (gerador.py), garantindo saida identica.
"""
import os
import tempfile
from datetime import date

import streamlit as st
import gerador

st.set_page_config(page_title="D'Coratto · Gerador de Propostas",
                   page_icon="📄", layout="centered")

# ------------------------------------------------------------------ estilo
st.markdown("""
<style>
  .stApp { background:#F4F1EC; }
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
modo = st.radio("", ["Sem arquiteto parceiro", "Adicionar arquiteto"],
                horizontal=True, label_visibility="collapsed")

arq = {"tipo": "nenhum"}
if modo == "Adicionar arquiteto":
    a1, a2 = st.columns(2)
    arq_nome = a1.text_input("Nome do arquiteto", placeholder="ex.: Arquiteto Diego")
    arq_insta = a2.text_input("Instagram", placeholder="@exemplararquitetura")
    arq_foto = st.file_uploader("Foto do arquiteto", type=["jpg", "jpeg", "png"], key="arqfoto")
    arq = {"tipo": "novo", "nome": arq_nome, "insta": arq_insta, "foto_raw": arq_foto}
    st.caption("O arquiteto aparece com destaque como autor do projeto.")
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
                foto_path = None
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
