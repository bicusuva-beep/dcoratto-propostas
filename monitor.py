# -*- coding: utf-8 -*-
"""Monitoramento: captura de erro e leitura de padroes.

Duas partes com confiabilidade bem diferente, e vale saber qual e qual:

  Erros    — fato. Excecao capturada com contexto. Nao ha interpretacao.
  Padroes  — regra explicita sobre os proprios dados ("mesmo cliente 3x em
             24h"). Cada achado diz o numero que o gerou, para voce julgar.
             Nao ha adivinhacao nem modelo estatistico: com dezenas de
             propostas por mes, qualquer inferencia mais sofisticada seria
             ruido vendido como insight.
"""
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone


def _dt(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        return None


def registrar_erro(bd, origem, exc, usuario="", proposta_id=None):
    """Guarda a excecao com a pilha. Nunca levanta erro por conta propria."""
    try:
        bd.evento("erro", origem, f"{type(exc).__name__}: {exc}",
                  traceback.format_exc(), usuario, proposta_id)
    except Exception:
        pass


def registrar_acao(bd, origem, mensagem, usuario="", proposta_id=None, detalhe=""):
    try:
        bd.evento("acao", origem, mensagem, detalhe, usuario, proposta_id)
    except Exception:
        pass


# ---------------------------------------------------------------- bugs
def resumo_erros(bd, dias=30):
    """Agrupa erros iguais: o que quebra mais aparece primeiro."""
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    evs = [e for e in bd.eventos("erro", limite=2000)
           if (_dt(e.get("criado_em")) or datetime.now(timezone.utc)) >= corte]
    grupos = defaultdict(lambda: {"n": 0, "ultimo": None, "origem": "", "exemplo": ""})
    for e in evs:
        ch = (e.get("origem", ""), (e.get("mensagem") or "")[:120])
        g = grupos[ch]
        g["n"] += 1
        g["origem"] = e.get("origem", "")
        g["mensagem"] = (e.get("mensagem") or "")[:120]
        d = _dt(e.get("criado_em"))
        if d and (g["ultimo"] is None or d > g["ultimo"]):
            g["ultimo"] = d
            g["exemplo"] = (e.get("detalhe") or "")[:1500]
    return sorted(grupos.values(), key=lambda g: -g["n"])


# ---------------------------------------------------------------- padroes
def sugestoes(bd, propostas=None, dias=90):
    """Achados com base em regra explicita. Cada um traz o numero que o gerou."""
    achados = []
    props = propostas if propostas is not None else bd.listar(limite=1000)
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    recentes = [p for p in props
                if (_dt(p.get("criado_em")) or datetime.now(timezone.utc)) >= corte]

    if len(recentes) < 5:
        achados.append({
            "nivel": "info",
            "titulo": "Ainda há poucos dados",
            "texto": f"Só {len(recentes)} proposta(s) nos últimos {dias} dias. "
                     "As leituras abaixo ficam mais confiáveis com mais histórico.",
        })

    # 1) retrabalho: mesmo cliente varias vezes em pouco tempo
    porcliente = defaultdict(list)
    for p in recentes:
        porcliente[(p.get("cliente") or "").strip().lower()].append(p)
    repetidos = []
    for cli, lista in porcliente.items():
        if len(lista) < 3 or not cli:
            continue
        datas = sorted(d for d in (_dt(p.get("criado_em")) for p in lista) if d)
        for i in range(len(datas) - 2):
            if (datas[i + 2] - datas[i]) <= timedelta(days=2):
                repetidos.append((cli, len(lista)))
                break
    if repetidos:
        achados.append({
            "nivel": "atencao",
            "titulo": "Proposta refeita do zero em vez de editada",
            "texto": "Clientes com 3 ou mais propostas criadas em até 2 dias: "
                     + ", ".join(f"{c} ({n})" for c, n in repetidos[:5])
                     + ". Vale checar se a equipe sabe que dá para carregar e editar.",
        })

    # 2) campo que quase ninguem preenche
    if len(recentes) >= 8:
        for campo, rotulo in (("pagamento", "Forma de pagamento"),
                              ("numero", "Nº da proposta")):
            vazios = sum(1 for p in recentes if not (p.get(campo) or "").strip())
            pct = vazios / len(recentes)
            if pct >= 0.8:
                achados.append({
                    "nivel": "sugestao",
                    "titulo": f"'{rotulo}' fica quase sempre vazio",
                    "texto": f"{vazios} de {len(recentes)} propostas ({pct*100:.0f}%). "
                             "Ou o campo não faz sentido no fluxo, ou está mal "
                             "posicionado no formulário.",
                })

    # 3) parcelamento incompleto — a causa do total parcelado sumir
    incompletas = 0
    for p in recentes:
        det = bd.carregar(p["id"])
        if not det:
            continue
        ams = det["ambientes"]
        com = sum(1 for a in ams if a.get("parcela"))
        if ams and 0 < com < len(ams):
            incompletas += 1
    if incompletas:
        achados.append({
            "nivel": "atencao",
            "titulo": "Parcelamento preenchido pela metade",
            "texto": f"{incompletas} proposta(s) têm parcela em alguns ambientes e "
                     "em outros não. Nesse caso a linha 'ou Nx de' do total não "
                     "aparece no PDF — é tudo ou nada.",
        })

    # 4) proposta parada
    paradas = [p for p in recentes if (p.get("status") or "rascunho") == "rascunho"
               and (_dt(p.get("atualizado_em")) or datetime.now(timezone.utc))
               < datetime.now(timezone.utc) - timedelta(days=15)]
    if paradas:
        achados.append({
            "nivel": "sugestao",
            "titulo": "Propostas paradas em rascunho",
            "texto": f"{len(paradas)} proposta(s) sem alteração há mais de 15 dias e "
                     "ainda como rascunho. Pode ser follow-up esquecido.",
        })

    # 5) ambiente recorrente vira modelo
    nomes = Counter()
    for p in recentes:
        det = bd.carregar(p["id"])
        if det:
            for a in det["ambientes"]:
                n = (a.get("nome") or "").strip().lower()
                if n:
                    nomes[n] += 1
    if len(recentes) >= 8:
        for nome, qtd in nomes.most_common(3):
            if qtd >= max(4, len(recentes) * 0.6):
                achados.append({
                    "nivel": "sugestao",
                    "titulo": f"'{nome}' se repete muito",
                    "texto": f"Aparece em {qtd} das {len(recentes)} propostas. "
                             "Vale virar um modelo pronto, com descrição padrão, "
                             "para não redigitar toda vez.",
                })

    # 6) erros recentes
    erros = resumo_erros(bd, dias=14)
    if erros:
        achados.append({
            "nivel": "erro",
            "titulo": "Erros nos últimos 14 dias",
            "texto": f"{sum(e['n'] for e in erros)} ocorrência(s) em "
                     f"{len(erros)} tipo(s). O mais frequente: "
                     f"{erros[0].get('mensagem','')} ({erros[0]['n']}x).",
        })
    return achados


# ---------------------------------------------------------------- indicadores
def indicadores(bd, propostas=None):
    props = propostas if propostas is not None else bd.listar(limite=2000)
    if not props:
        return {"total": 0}
    valores = [float(p.get("total") or 0) for p in props]
    agora = datetime.now(timezone.utc)
    mes = [p for p in props
           if (_dt(p.get("criado_em")) or agora) >= agora - timedelta(days=30)]
    por_status = Counter((p.get("status") or "rascunho") for p in props)
    por_mes = defaultdict(float)
    cont_mes = Counter()
    for p in props:
        d = _dt(p.get("criado_em"))
        if d:
            ch = d.strftime("%Y-%m")
            por_mes[ch] += float(p.get("total") or 0)
            cont_mes[ch] += 1
    return {
        "total": len(props),
        "no_mes": len(mes),
        "valor_total": sum(valores),
        "ticket_medio": (sum(valores) / len(valores)) if valores else 0,
        "maior": max(valores) if valores else 0,
        "menor": min(valores) if valores else 0,
        "por_status": dict(por_status),
        "valor_por_mes": dict(sorted(por_mes.items())),
        "qtd_por_mes": dict(sorted(cont_mes.items())),
    }
