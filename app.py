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
import dados
import monitor

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



def _nome_arquivo(cliente, proposta=""):
    """Nome de arquivo a prova de navegador: sem acento e sem espaco.

    Acento e espaco no cabecalho de download sao truncados ou renomeados por
    alguns navegadores — era por isso que o PDF saia sem o nome do cliente.
    """
    import unicodedata
    base = unicodedata.normalize("NFKD", cliente or "").encode("ascii", "ignore").decode()
    base = "".join(ch if (ch.isalnum() or ch in " -_") else "" for ch in base)
    base = "_".join(base.split()) or "Cliente"
    num = "".join(ch for ch in (proposta or "") if ch.isalnum() or ch == "-")
    return f"Proposta_{base}{'_' + num if num else ''}.pdf"


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

# ------------------------------------------------------------------ acesso
BD = dados.banco()
st.session_state.setdefault("f_validade", "10 dias")
st.session_state.setdefault("f_parcelas", 12)
st.session_state.setdefault("f_parcela_total", 0.0)
st.session_state.setdefault("f_texto_parc", "")

# Sem login, por decisao do cliente. Quem gravar aparece como "equipe".
# Se um dia entrar autenticacao, e so voltar a chamar auth.tela_login aqui.
USUARIO = {"nome": "Equipe D'Coratto", "email": "equipe", "admin": True}

# Um pedido de troca de secao e aplicado ANTES do radio existir. O Streamlit
# nao deixa alterar a chave de um widget ja criado — foi o que quebrou antes.
_OPCOES = ["Nova proposta", "Propostas salvas", "Painel comercial", "Monitoramento"]
if "_ir_para" in st.session_state:
    st.session_state["_secao"] = st.session_state.pop("_ir_para")
st.session_state.setdefault("_secao", _OPCOES[0])

with st.sidebar:
    SECAO = st.radio("Menu", _OPCOES, key="_secao", label_visibility="collapsed")
    st.divider()
    st.caption(f"Dados em: {dados.qual_backend()}")

# ------------------------------------------------------------------ carregar
# Uma proposta pedida na tela de busca e aplicada AQUI, antes de qualquer
# widget existir — o Streamlit nao deixa alterar o estado de um widget ja criado.
if "_abrir" in st.session_state:
    _pid = st.session_state.pop("_abrir")
    _d = BD.carregar(_pid)
    if _d:
        _p, _ams = _d["proposta"], _d["ambientes"]
        for _k in list(st.session_state.keys()):
            if _k[:4] in ("nome", "desc", "valo", "parc", "foto"):
                st.session_state.pop(_k, None)
        st.session_state.slots = list(range(len(_ams)))
        st.session_state.prox_id = len(_ams) + 1000
        st.session_state["_editando"] = _pid
        st.session_state["f_cliente"] = _p.get("cliente", "")
        st.session_state["f_numero"] = _p.get("numero", "")
        st.session_state["f_validade"] = _p.get("validade", "10 dias")
        st.session_state["f_pagamento"] = _p.get("pagamento", "")
        st.session_state["f_parcelas"] = int(_p.get("parcelas") or 12)
        st.session_state["f_texto_parc"] = _p.get("texto_parcelamento", "") or ""
        st.session_state["f_parcela_total"] = float(_p.get("parcela_total") or 0)
        st.session_state["_arq_salvo"] = _p.get("arquiteto") or {}
        for _i, _a in enumerate(_ams):
            st.session_state[f"nome{_i}"] = _a.get("nome", "")
            st.session_state[f"desc{_i}"] = _a.get("descricao", "")
            st.session_state[f"valor{_i}"] = float(_a.get("valor") or 0)
            st.session_state[f"parc{_i}"] = float(_a.get("parcela") or 0)
            st.session_state[f"salvas{_i}"] = list(_a.get("fotos") or [])

st.markdown('<div class="dco-title">Gerador de <i>Propostas</i></div>', unsafe_allow_html=True)

# ==================================================================== SEÇÕES
if SECAO == "Nova proposta":
    _ed = st.session_state.get("_editando")
    if _ed:
        st.info(f"Editando a proposta #{_ed}. Ao gerar, você escolhe entre "
                "substituir esta ou salvar como nova.")
        if st.button("↩ Começar uma proposta em branco"):
            for _k in list(st.session_state.keys()):
                if _k[:4] in ("nome", "desc", "valo", "parc", "foto", "salv") or \
                   _k.startswith("f_") or _k in ("_editando", "_arq_salvo"):
                    st.session_state.pop(_k, None)
            st.session_state.slots = [0]
            st.session_state.prox_id = 1
            st.rerun()


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
    cliente = c1.text_input("Cliente", key="f_cliente", placeholder="Nome do cliente")
    proposta = c2.text_input("Nº da proposta (opcional)", key="f_numero", placeholder="ex.: 2026-014")
    c3, c4 = st.columns(2)
    validade = c3.text_input("Validade da proposta", key="f_validade")
    pagamento = c4.text_input("Forma de pagamento (opcional)", key="f_pagamento",
                              placeholder="ex.: 40% entrada + 12x no cartão")
    cp1, cp2 = st.columns(2)
    n_parcelas = cp1.number_input("Parcelar em até quantas vezes", min_value=1, max_value=48,
                                  key="f_parcelas", step=1,
                                  help="Usado nas linhas 'ou Nx de R$ ...' do PDF.")
    texto_parc = st.text_input("Linha do parcelamento no PDF (opcional)",
                               key="f_texto_parc",
                               placeholder="ex.: Entrada de R$ 50.000,00 + 11x de R$ 28.000,00 no Cartão",
                               help="Sai logo abaixo do valor total. Se deixar vazio, o PDF "
                                    "monta sozinho 'ou Nx de R$ ...' com o valor ao lado.")
    parcela_total = cp2.number_input("Valor da parcela do total (R$) — opcional",
                                     key="f_parcela_total", min_value=0.0, step=100.0,
                                     format="%.2f",
                                     help="Preencha só aqui se o parcelamento for do "
                                          "valor final. Sem isso, a linha 'ou Nx de' só "
                                          "aparece se TODOS os ambientes tiverem parcela.")


    # ------------------------------------------------------------------ ambientes
    st.markdown('<div class="dco-kicker">Ambientes</div>', unsafe_allow_html=True)

    cadd, cdel = st.columns([1, 1])
    # O novo ambiente entra no TOPO da lista: fica logo abaixo do botao, sem
    # precisar rolar a pagina para preencher.
    if cadd.button("➕ Adicionar ambiente"):
        st.session_state.slots.insert(0, st.session_state.prox_id)
        st.session_state.prox_id += 1
    # Remove tambem pelo topo, para ser simetrico: apaga o que acabou de ser criado.
    if cdel.button("➖ Remover o de cima") and len(st.session_state.slots) > 1:
        _sid = st.session_state.slots.pop(0)
        for _k in (f"nome{_sid}", f"desc{_sid}", f"valor{_sid}", f"parc{_sid}", f"fotos{_sid}"):
            st.session_state.pop(_k, None)

    st.caption("O ambiente novo entra aqui em cima. A ordem desta tela é a ordem do PDF — "
               "use ▲ ▼ para trocar.")

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
            # fotos que ja estavam gravadas: aparecem aqui e nao precisam subir de novo
            _salvas = st.session_state.get(f"salvas{sid}") or []
            if _salvas:
                st.caption(f"{len(_salvas)} foto(s) já salva(s) nesta proposta")
                _cols = st.columns(max(len(_salvas), 1))
                _manter = []
                for _i, _cam in enumerate(_salvas):
                    with _cols[_i]:
                        _b = BD.ler_arquivo(_cam)
                        if _b:
                            st.image(_b, width=110)
                        if not st.checkbox("remover", key=f"rm{sid}_{_i}"):
                            _manter.append(_cam)
                st.session_state[f"manter{sid}"] = _manter
            fotos = st.file_uploader("Fotos do ambiente (1 a 4 — todas entram na página "
                                     "do ambiente)", key=f"fotos{sid}",
                                     type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            ambientes.append({"nome": nome, "desc": desc, "valor": valor,
                              "parcela": parcela if parcela > 0 else None,
                              "fotos_raw": fotos[:4] if fotos else [],
                              "fotos_salvas": st.session_state.get(f"manter{sid}", _salvas),
                              "sid": sid})

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
        _exc = st.checkbox("Mostrar apenas este arquiteto na proposta",
                           key="exc_lista",
                           help="Marque quando o arquiteto não quiser os demais na página.")
        arq = {"tipo": "novo", "nome": _reg["nome"],
               "insta": _reg.get("insta", ""), "foto_path": _fp, "exclusivo": _exc}
        st.caption("O arquiteto aparece com destaque como autor do projeto."
                   + (" A rede de parceiros não entra." if _exc else ""))

    elif modo == "Cadastrar novo":
        a1, a2 = st.columns(2)
        arq_nome = a1.text_input("Nome do arquiteto", placeholder="ex.: Arquiteto Diego")
        arq_insta = a2.text_input("Instagram", placeholder="@exemplararquitetura")
        arq_foto = st.file_uploader("Foto do arquiteto", type=["jpg", "jpeg", "png"], key="arqfoto")
        _exc = st.checkbox("Mostrar apenas este arquiteto na proposta",
                           key="exc_novo",
                           help="Marque quando o arquiteto não quiser os demais na página.")
        arq = {"tipo": "novo", "nome": arq_nome, "insta": arq_insta,
               "foto_raw": arq_foto, "exclusivo": _exc}
        st.caption("O arquiteto aparece com destaque como autor do projeto."
                   + (" A rede de parceiros não entra." if _exc else ""))
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
        _sem_foto = [f"{i + 1:02d}" for i, a in enumerate(ambientes)
                     if not a["fotos_raw"] and not a.get("fotos_salvas")]
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
                    paths, guardar = [], []
                    # as que ja estavam gravadas voltam do banco
                    for j, cam in enumerate(a.get("fotos_salvas") or []):
                        b = BD.ler_arquivo(cam)
                        if not b:
                            continue
                        p = os.path.join(tmp, f"amb{i}_s{j}.jpg")
                        with open(p, "wb") as out:
                            out.write(b)
                        paths.append(p)
                        guardar.append(cam)
                    # e as novas que a pessoa acabou de subir
                    for j, f in enumerate(a["fotos_raw"]):
                        p = os.path.join(tmp, f"amb{i}_{j}.jpg")
                        with open(p, "wb") as out:
                            out.write(f.getbuffer())
                        paths.append(p)
                        guardar.append(("NOVA", p))
                    amb_final.append({"nome": a["nome"], "desc": a["desc"],
                                      "valor": a["valor"], "parcela": a["parcela"],
                                      "fotos": paths[:4], "guardar": guardar[:4]})

                arq_final = {"tipo": "nenhum"}
                if arq["tipo"] == "novo":
                    foto_path = arq.get("foto_path")
                    if arq.get("foto_raw"):
                        foto_path = os.path.join(tmp, "arq.jpg")
                        with open(foto_path, "wb") as out:
                            out.write(arq["foto_raw"].getbuffer())
                    if arq.get("nome") or foto_path:
                        arq_final = {"tipo": "novo", "nome": arq.get("nome", ""),
                                     "insta": arq.get("insta", ""), "foto": foto_path,
                                     "exclusivo": bool(arq.get("exclusivo"))}

                payload = {
                    "cliente": cliente.strip(),
                    "proposta": proposta.strip(),
                    "data": date.today().strftime("%d/%m/%Y"),
                    "validade": validade.strip() or "10 dias",
                    "pagamento": pagamento.strip(),
                    "parcelas": int(n_parcelas),
                    "parcela_total": parcela_total or None,
                    "texto_parcelamento": texto_parc.strip(),
                    "ambientes": amb_final,
                    "arquiteto": arq_final,
                }

                saida = os.path.join(tmp, "proposta.pdf")
                try:
                    gerador.gerar(payload, saida)
                except Exception as exc:
                    monitor.registrar_erro(BD, "gerar_pdf", exc, USUARIO["email"],
                                           st.session_state.get("_editando"))
                    st.error("Não foi possível gerar o PDF. O erro foi registrado "
                             "no painel de Monitoramento.")
                    st.stop()
                with open(saida, "rb") as f:
                    pdf_bytes = f.read()

            st.success("Proposta gerada.")
            nome_arq = _nome_arquivo(cliente, proposta)
            st.download_button("⬇ Baixar PDF", data=pdf_bytes, file_name=nome_arq,
                               mime="application/pdf")

            # guarda o necessario para salvar sem ter que gerar de novo
            st.session_state["_pronta"] = {
                "payload": {k: v for k, v in payload.items() if k != "ambientes"},
                "ambientes": [{"nome": a["nome"], "desc": a["desc"], "valor": a["valor"],
                               "parcela": a["parcela"], "guardar": a["guardar"]}
                              for a in amb_final],
            }

    # ------------------------------------------------------------------ salvar
    if st.session_state.get("_pronta"):
        st.markdown('<div class="dco-kicker">Salvar no sistema</div>',
                    unsafe_allow_html=True)
        _pr = st.session_state["_pronta"]
        _ed = st.session_state.get("_editando")

        def _grava(pid_destino, rotulo):
            """Grava proposta e sobe as fotos novas para o armazenamento."""
            try:
                base = dict(_pr["payload"])
                if pid_destino is None and _ed:
                    base["origem_id"] = _ed        # cópia guarda de onde veio
                ams = []
                for a in _pr["ambientes"]:
                    ams.append({"nome": a["nome"], "desc": a["desc"],
                                "valor": a["valor"], "parcela": a["parcela"],
                                "fotos": []})
                pid = BD.salvar_proposta(base, ams, USUARIO["email"], pid_destino)
                # agora que existe id, sobe as fotos e grava os caminhos
                for i, a in enumerate(_pr["ambientes"]):
                    caminhos = []
                    for j, g in enumerate(a["guardar"]):
                        if isinstance(g, tuple):           # foto nova
                            with open(g[1], "rb") as fh:
                                cam = f"propostas/{pid}/{i}/{j}.jpg"
                                BD.salvar_arquivo(cam, fh.read())
                            caminhos.append(cam)
                        else:                              # ja estava salva
                            caminhos.append(g)
                    ams[i]["fotos"] = caminhos
                BD.salvar_proposta(base, ams, USUARIO["email"], pid)
                monitor.registrar_acao(BD, "proposta", rotulo, USUARIO["email"], pid)
                st.session_state.pop("_pronta", None)
                st.session_state["_editando"] = pid
                st.success(f"{rotulo}. Proposta #{pid}.")
                st.rerun()
            except Exception as exc:
                monitor.registrar_erro(BD, "salvar", exc, USUARIO["email"], pid_destino)
                st.error("Não consegui salvar. O erro foi registrado no "
                         "painel de Monitoramento.")

        if _ed:
            b1, b2 = st.columns(2)
            if b1.button("💾 Substituir a proposta atual", type="primary"):
                _grava(_ed, "Proposta atualizada")
            if b2.button("📄 Salvar como nova"):
                _grava(None, "Proposta salva como nova")
            st.caption("Substituir guarda a versão anterior no histórico — "
                       "nada é perdido.")
        else:
            if st.button("💾 Salvar proposta", type="primary"):
                _grava(None, "Proposta salva")

# ==================================================================== PROPOSTAS
elif SECAO == "Propostas salvas":
    st.markdown('<div class="dco-sub">Busque, abra e edite uma proposta já criada.</div>',
                unsafe_allow_html=True)
    busca = st.text_input("Buscar por cliente ou número", placeholder="ex.: Vanessa")
    lista = BD.listar(busca=busca.strip())
    if not lista:
        st.info("Nenhuma proposta encontrada." if busca else
                "Nenhuma proposta salva ainda. Crie uma em 'Nova proposta'.")
    for p in lista:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
            c1.markdown(f"**{p.get('cliente') or '(sem cliente)'}**")
            c1.caption(f"#{p['id']}"
                       + (f" · nº {p['numero']}" if p.get("numero") else "")
                       + f" · v{p.get('versao', 1)}"
                       + (f" · cópia de #{p['origem_id']}" if p.get("origem_id") else ""))
            c2.markdown(f"R$ {_br(float(p.get('total') or 0))}")
            _st_atual = p.get("status") or "rascunho"
            _novo = c3.selectbox("Status", ["rascunho", "enviada", "aprovada", "recusada"],
                                 index=["rascunho", "enviada", "aprovada", "recusada"]
                                 .index(_st_atual), key=f"stt{p['id']}",
                                 label_visibility="collapsed")
            if _novo != _st_atual:
                BD.definir_status(p["id"], _novo)
                monitor.registrar_acao(BD, "status", f"{_st_atual} → {_novo}",
                                       USUARIO["email"], p["id"])
                st.rerun()
            if c4.button("Abrir", key=f"ab{p['id']}"):
                st.session_state["_abrir"] = p["id"]
                st.session_state["_ir_para"] = "Nova proposta"
                st.session_state.pop("_pronta", None)
                st.rerun()

# ==================================================================== PAINEL
elif SECAO == "Painel comercial":
    st.markdown('<div class="dco-sub">Visão do que foi proposto. '
                'Tudo sai das propostas salvas.</div>', unsafe_allow_html=True)
    props = BD.listar(limite=2000)
    ind = monitor.indicadores(BD, props)
    if not ind.get("total"):
        st.info("Ainda não há propostas salvas para analisar.")
    else:
        a, b, c, d = st.columns(4)
        a.metric("Propostas", ind["total"])
        b.metric("Nos últimos 30 dias", ind["no_mes"])
        c.metric("Valor total proposto", f"R$ {_br(ind['valor_total'])}")
        d.metric("Ticket médio", f"R$ {_br(ind['ticket_medio'])}")

        st.markdown('<div class="dco-kicker">Por mês</div>', unsafe_allow_html=True)
        e1, e2 = st.columns(2)
        with e1:
            st.caption("Valor proposto")
            st.bar_chart(ind["valor_por_mes"])
        with e2:
            st.caption("Quantidade")
            st.bar_chart(ind["qtd_por_mes"])

        st.markdown('<div class="dco-kicker">Situação</div>', unsafe_allow_html=True)
        f1, f2 = st.columns([1, 1])
        with f1:
            for k in ("rascunho", "enviada", "aprovada", "recusada"):
                st.write(f"**{k.capitalize()}**: {ind['por_status'].get(k, 0)}")
            _fech = ind["por_status"].get("aprovada", 0) + ind["por_status"].get("recusada", 0)
            if _fech:
                _conv = ind["por_status"].get("aprovada", 0) / _fech * 100
                st.metric("Aproveitamento", f"{_conv:.0f}%",
                          help="Aprovadas sobre o total já decidido "
                               "(aprovadas + recusadas). Rascunhos e enviadas "
                               "não entram na conta.")
            else:
                st.caption("Sem propostas decididas ainda — marque o status para "
                           "acompanhar aproveitamento.")
        with f2:
            st.write(f"**Maior proposta:** R$ {_br(ind['maior'])}")
            st.write(f"**Menor proposta:** R$ {_br(ind['menor'])}")

        st.markdown('<div class="dco-kicker">Ambientes e arquitetos</div>',
                    unsafe_allow_html=True)
        from collections import Counter
        amb_cont, arq_cont = Counter(), Counter()
        for p in props:
            det = BD.carregar(p["id"])
            if not det:
                continue
            for a in det["ambientes"]:
                if (a.get("nome") or "").strip():
                    amb_cont[a["nome"].strip()] += 1
            _a = det["proposta"].get("arquiteto") or {}
            if _a.get("nome"):
                arq_cont[_a["nome"]] += 1
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Ambientes mais frequentes")
            for n, q in amb_cont.most_common(8):
                st.write(f"{q}× · {n}")
            if not amb_cont:
                st.caption("—")
        with g2:
            st.caption("Arquitetos mais indicados")
            for n, q in arq_cont.most_common(8):
                st.write(f"{q}× · {n}")
            if not arq_cont:
                st.caption("—")

# ==================================================================== MONITOR
elif SECAO == "Monitoramento":
    st.markdown('<div class="dco-sub">Erros do sistema e leituras do processo.</div>',
                unsafe_allow_html=True)
    t1, t2 = st.tabs(["Sugestões", "Erros"])

    with t1:
        st.caption("Cada item vem de uma regra explícita sobre os seus dados, "
                   "com o número que a gerou. Não há adivinhação.")
        achados = monitor.sugestoes(BD)
        if not achados:
            st.success("Nada a apontar no momento.")
        _cor = {"erro": "🔴", "atencao": "🟡", "sugestao": "🔵", "info": "⚪"}
        for s in achados:
            with st.container(border=True):
                st.markdown(f"{_cor.get(s['nivel'], '•')} **{s['titulo']}**")
                st.write(s["texto"])

    with t2:
        erros = monitor.resumo_erros(BD, dias=30)
        if not erros:
            st.success("Nenhum erro registrado nos últimos 30 dias.")
        for e in erros:
            with st.expander(f"{e['n']}× · [{e['origem']}] {e.get('mensagem','')}"):
                st.caption(f"Última ocorrência: {e.get('ultimo')}")
                st.code(e.get("exemplo", "")[:1500])
