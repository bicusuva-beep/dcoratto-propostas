# -*- coding: utf-8 -*-
"""Persistencia das propostas.

Dois backends com a MESMA interface:

  SQLite  — usado quando nao ha credencial do Supabase. Serve para rodar na
            maquina local e, principalmente, para eu conseguir testar toda a
            logica sem depender de chave de producao.
  Supabase — usado quando SUPABASE_URL e SUPABASE_KEY existem.

A escolha e automatica. O resto do app nao sabe qual esta em uso.
"""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone

try:
    import requests
except Exception:                       # o Streamlit ja traz requests
    requests = None


# ---------------------------------------------------------------- utilidades
def agora():
    return datetime.now(timezone.utc).isoformat()


def _num(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


# ================================================================= SQLite
class BancoLocal:
    """Backend de arquivo. Bom para desenvolver e testar."""

    def __init__(self, caminho=None):
        self.caminho = caminho or os.environ.get(
            "DCO_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "propostas.db"))
        self._cria()

    def _con(self):
        c = sqlite3.connect(self.caminho)
        c.row_factory = sqlite3.Row
        return c

    def _cria(self):
        with self._con() as c:
            c.executescript("""
            create table if not exists usuarios(
                id integer primary key autoincrement,
                email text unique not null, nome text not null,
                senha_hash text not null, ativo integer default 1,
                admin integer default 0, criado_em text, ultimo_acesso text);
            create table if not exists propostas(
                id integer primary key autoincrement,
                cliente text not null, numero text default '',
                validade text default '10 dias', pagamento text default '',
                parcelas integer default 12, arquiteto text default '{}',
                parcela_total real, texto_parcelamento text default '',
                status text default 'rascunho', versao integer default 1,
                origem_id integer, total real default 0,
                criado_por text default '', criado_em text, atualizado_em text,
                arquivada integer default 0);
            create table if not exists ambientes(
                id integer primary key autoincrement,
                proposta_id integer not null, ordem integer not null,
                nome text default '', descricao text default '',
                valor real default 0, parcela real, fotos text default '[]');
            create table if not exists versoes(
                id integer primary key autoincrement,
                proposta_id integer not null, versao integer not null,
                conteudo text not null, criado_por text, criado_em text);
            create table if not exists eventos(
                id integer primary key autoincrement,
                tipo text not null, origem text default '',
                mensagem text default '', detalhe text default '',
                usuario text default '', proposta_id integer, criado_em text);
            """)

    # -------------------------------------------------------- propostas
    def salvar_proposta(self, dados, ambientes, usuario="", proposta_id=None):
        total = sum(_num(a.get("valor")) for a in ambientes)
        with self._con() as c:
            if proposta_id:
                ant = self.carregar(proposta_id)
                if ant:
                    c.execute("insert into versoes(proposta_id,versao,conteudo,"
                              "criado_por,criado_em) values(?,?,?,?,?)",
                              (proposta_id, ant["proposta"]["versao"],
                               json.dumps(ant, ensure_ascii=False), usuario, agora()))
                c.execute("""update propostas set cliente=?,numero=?,validade=?,
                          pagamento=?,parcelas=?,parcela_total=?,texto_parcelamento=?,
                          arquiteto=?,total=?,versao=versao+1,atualizado_em=? where id=?""",
                          (dados.get("cliente",""), dados.get("proposta",""),
                           dados.get("validade",""), dados.get("pagamento",""),
                           int(dados.get("parcelas") or 12),
                           _num(dados.get("parcela_total")) or None,
                           dados.get("texto_parcelamento",""),
                           json.dumps(dados.get("arquiteto") or {}, ensure_ascii=False),
                           total, agora(), proposta_id))
                c.execute("delete from ambientes where proposta_id=?", (proposta_id,))
                pid = proposta_id
            else:
                cur = c.execute("""insert into propostas(cliente,numero,validade,
                    pagamento,parcelas,parcela_total,texto_parcelamento,arquiteto,
                    total,origem_id,criado_por,criado_em,atualizado_em)
                    values(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (dados.get("cliente",""), dados.get("proposta",""),
                     dados.get("validade",""), dados.get("pagamento",""),
                     int(dados.get("parcelas") or 12),
                     _num(dados.get("parcela_total")) or None,
                     dados.get("texto_parcelamento",""),
                     json.dumps(dados.get("arquiteto") or {}, ensure_ascii=False),
                     total, dados.get("origem_id"), usuario, agora(), agora()))
                pid = cur.lastrowid
            for i, a in enumerate(ambientes):
                c.execute("""insert into ambientes(proposta_id,ordem,nome,descricao,
                          valor,parcela,fotos) values(?,?,?,?,?,?,?)""",
                          (pid, i, a.get("nome",""), a.get("desc",""),
                           _num(a.get("valor")),
                           _num(a.get("parcela")) if a.get("parcela") else None,
                           json.dumps(a.get("fotos") or [], ensure_ascii=False)))
        return pid

    def carregar(self, proposta_id):
        with self._con() as c:
            p = c.execute("select * from propostas where id=?", (proposta_id,)).fetchone()
            if not p:
                return None
            ams = c.execute("select * from ambientes where proposta_id=? order by ordem",
                            (proposta_id,)).fetchall()
        prop = dict(p)
        prop["arquiteto"] = json.loads(prop.get("arquiteto") or "{}")
        return {"proposta": prop,
                "ambientes": [{**dict(a), "fotos": json.loads(a["fotos"] or "[]")}
                              for a in ams]}

    def listar(self, busca="", limite=200):
        q = "select * from propostas where arquivada=0"
        args = []
        if busca:
            q += " and (lower(cliente) like ? or numero like ?)"
            args += [f"%{busca.lower()}%", f"%{busca}%"]
        q += " order by atualizado_em desc limit ?"
        args.append(limite)
        with self._con() as c:
            return [dict(r) for r in c.execute(q, args).fetchall()]

    def definir_status(self, proposta_id, status):
        with self._con() as c:
            c.execute("update propostas set status=?,atualizado_em=? where id=?",
                      (status, agora(), proposta_id))

    def versoes(self, proposta_id):
        with self._con() as c:
            return [dict(r) for r in c.execute(
                "select id,versao,criado_por,criado_em from versoes "
                "where proposta_id=? order by versao desc", (proposta_id,)).fetchall()]

    # -------------------------------------------------------- eventos
    def evento(self, tipo, origem, mensagem, detalhe="", usuario="", proposta_id=None):
        with self._con() as c:
            c.execute("""insert into eventos(tipo,origem,mensagem,detalhe,usuario,
                      proposta_id,criado_em) values(?,?,?,?,?,?,?)""",
                      (tipo, origem, mensagem[:500], detalhe[:4000], usuario,
                       proposta_id, agora()))

    def eventos(self, tipo=None, limite=500):
        q = "select * from eventos"
        args = []
        if tipo:
            q += " where tipo=?"
            args.append(tipo)
        q += " order by criado_em desc limit ?"
        args.append(limite)
        with self._con() as c:
            return [dict(r) for r in c.execute(q, args).fetchall()]

    # -------------------------------------------------------- usuarios
    def usuario_por_email(self, email):
        with self._con() as c:
            r = c.execute("select * from usuarios where lower(email)=?",
                          (email.lower().strip(),)).fetchone()
        return dict(r) if r else None

    def criar_usuario(self, email, nome, senha_hash, admin=False):
        with self._con() as c:
            c.execute("""insert into usuarios(email,nome,senha_hash,admin,criado_em)
                      values(?,?,?,?,?)""",
                      (email.lower().strip(), nome, senha_hash, 1 if admin else 0, agora()))

    def listar_usuarios(self):
        with self._con() as c:
            return [dict(r) for r in c.execute(
                "select id,email,nome,ativo,admin,ultimo_acesso from usuarios "
                "order by nome").fetchall()]

    def marcar_acesso(self, email):
        with self._con() as c:
            c.execute("update usuarios set ultimo_acesso=? where lower(email)=?",
                      (agora(), email.lower().strip()))

    # -------------------------------------------------------- arquivos
    def salvar_arquivo(self, caminho, conteudo):
        destino = os.path.join(os.path.dirname(os.path.abspath(self.caminho)),
                               "arquivos", caminho)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            f.write(conteudo)
        return caminho

    def ler_arquivo(self, caminho):
        destino = os.path.join(os.path.dirname(os.path.abspath(self.caminho)),
                               "arquivos", caminho)
        if not os.path.exists(destino):
            return None
        with open(destino, "rb") as f:
            return f.read()


# ================================================================= Supabase
class BancoSupabase:
    """Backend de producao, via PostgREST e Storage."""

    def __init__(self, url, chave, bucket=None):
        # O nome do bucket diferencia maiuscula. O criado no painel e "Propostas".
        # Da para trocar pelo .env sem mexer no codigo.
        bucket = bucket or os.environ.get("SUPABASE_BUCKET", "Propostas")
        self.url = url.rstrip("/")
        self.chave = chave
        self.bucket = bucket
        self.h = {"apikey": chave, "Authorization": f"Bearer {chave}",
                  "Content-Type": "application/json"}

    def _rest(self, tabela):
        return f"{self.url}/rest/v1/{tabela}"

    def _get(self, tabela, params):
        r = requests.get(self._rest(tabela), headers=self.h, params=params, timeout=25)
        r.raise_for_status()
        return r.json()

    def _post(self, tabela, corpo, prefer="return=representation"):
        h = dict(self.h); h["Prefer"] = prefer
        r = requests.post(self._rest(tabela), headers=h,
                          data=json.dumps(corpo, ensure_ascii=False).encode(), timeout=25)
        r.raise_for_status()
        return r.json() if r.text else []

    def _patch(self, tabela, params, corpo):
        h = dict(self.h); h["Prefer"] = "return=representation"
        r = requests.patch(self._rest(tabela), headers=h, params=params,
                           data=json.dumps(corpo, ensure_ascii=False).encode(), timeout=25)
        r.raise_for_status()
        return r.json() if r.text else []

    def _delete(self, tabela, params):
        r = requests.delete(self._rest(tabela), headers=self.h, params=params, timeout=25)
        r.raise_for_status()

    # -------------------------------------------------------- propostas
    def salvar_proposta(self, dados, ambientes, usuario="", proposta_id=None):
        total = sum(_num(a.get("valor")) for a in ambientes)
        corpo = {"cliente": dados.get("cliente", ""),
                 "numero": dados.get("proposta", ""),
                 "validade": dados.get("validade", ""),
                 "pagamento": dados.get("pagamento", ""),
                 "parcelas": int(dados.get("parcelas") or 12),
                 "parcela_total": _num(dados.get("parcela_total")) or None,
                 "texto_parcelamento": dados.get("texto_parcelamento", ""),
                 "arquiteto": dados.get("arquiteto") or {},
                 "total": total, "atualizado_em": agora()}
        if proposta_id:
            ant = self.carregar(proposta_id)
            if ant:
                self._post("versoes", {"proposta_id": proposta_id,
                                       "versao": ant["proposta"].get("versao", 1),
                                       "conteudo": ant, "criado_por": usuario},
                           prefer="return=minimal")
            corpo["versao"] = (ant["proposta"].get("versao", 1) + 1) if ant else 1
            self._patch("propostas", {"id": f"eq.{proposta_id}"}, corpo)
            self._delete("ambientes", {"proposta_id": f"eq.{proposta_id}"})
            pid = proposta_id
        else:
            corpo.update({"criado_por": usuario, "criado_em": agora(),
                          "origem_id": dados.get("origem_id")})
            pid = self._post("propostas", corpo)[0]["id"]
        linhas = [{"proposta_id": pid, "ordem": i, "nome": a.get("nome", ""),
                   "descricao": a.get("desc", ""), "valor": _num(a.get("valor")),
                   "parcela": _num(a.get("parcela")) if a.get("parcela") else None,
                   "fotos": a.get("fotos") or []} for i, a in enumerate(ambientes)]
        if linhas:
            self._post("ambientes", linhas, prefer="return=minimal")
        return pid

    def carregar(self, proposta_id):
        p = self._get("propostas", {"id": f"eq.{proposta_id}", "select": "*"})
        if not p:
            return None
        ams = self._get("ambientes", {"proposta_id": f"eq.{proposta_id}",
                                      "select": "*", "order": "ordem.asc"})
        return {"proposta": p[0], "ambientes": ams}

    def listar(self, busca="", limite=200):
        params = {"select": "*", "arquivada": "eq.false",
                  "order": "atualizado_em.desc", "limit": limite}
        if busca:
            params["or"] = f"(cliente.ilike.*{busca}*,numero.ilike.*{busca}*)"
        return self._get("propostas", params)

    def definir_status(self, proposta_id, status):
        self._patch("propostas", {"id": f"eq.{proposta_id}"},
                    {"status": status, "atualizado_em": agora()})

    def versoes(self, proposta_id):
        return self._get("versoes", {"proposta_id": f"eq.{proposta_id}",
                                     "select": "id,versao,criado_por,criado_em",
                                     "order": "versao.desc"})

    # -------------------------------------------------------- eventos
    def evento(self, tipo, origem, mensagem, detalhe="", usuario="", proposta_id=None):
        try:
            self._post("eventos", {"tipo": tipo, "origem": origem,
                                   "mensagem": mensagem[:500], "detalhe": detalhe[:4000],
                                   "usuario": usuario, "proposta_id": proposta_id},
                       prefer="return=minimal")
        except Exception:
            pass            # registro de evento nunca pode derrubar o app

    def eventos(self, tipo=None, limite=500):
        params = {"select": "*", "order": "criado_em.desc", "limit": limite}
        if tipo:
            params["tipo"] = f"eq.{tipo}"
        return self._get("eventos", params)

    # -------------------------------------------------------- usuarios
    def usuario_por_email(self, email):
        r = self._get("usuarios", {"email": f"eq.{email.lower().strip()}", "select": "*"})
        return r[0] if r else None

    def criar_usuario(self, email, nome, senha_hash, admin=False):
        self._post("usuarios", {"email": email.lower().strip(), "nome": nome,
                                "senha_hash": senha_hash, "admin": admin},
                   prefer="return=minimal")

    def listar_usuarios(self):
        return self._get("usuarios", {"select": "id,email,nome,ativo,admin,ultimo_acesso",
                                      "order": "nome.asc"})

    def marcar_acesso(self, email):
        self._patch("usuarios", {"email": f"eq.{email.lower().strip()}"},
                    {"ultimo_acesso": agora()})

    # -------------------------------------------------------- arquivos
    def salvar_arquivo(self, caminho, conteudo):
        url = f"{self.url}/storage/v1/object/{self.bucket}/{caminho}"
        h = {"apikey": self.chave, "Authorization": f"Bearer {self.chave}",
             "Content-Type": "application/octet-stream", "x-upsert": "true"}
        r = requests.post(url, headers=h, data=conteudo, timeout=60)
        if r.status_code >= 400:
            r = requests.put(url, headers=h, data=conteudo, timeout=60)
        r.raise_for_status()
        return caminho

    def ler_arquivo(self, caminho):
        url = f"{self.url}/storage/v1/object/{self.bucket}/{caminho}"
        r = requests.get(url, headers={"apikey": self.chave,
                                       "Authorization": f"Bearer {self.chave}"},
                         timeout=60)
        return r.content if r.status_code == 200 else None


# ================================================================= fabrica
_banco = None


def banco():
    """Devolve o backend adequado. Supabase se houver credencial, senao SQLite."""
    global _banco
    if _banco is not None:
        return _banco
    url = os.environ.get("SUPABASE_URL", "")
    chave = os.environ.get("SUPABASE_KEY", "")
    if not url or not chave:
        try:
            import streamlit as st
            url = url or st.secrets.get("SUPABASE_URL", "")
            chave = chave or st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass
    if url and chave and requests is not None:
        _banco = BancoSupabase(url, chave)
    else:
        _banco = BancoLocal()
    return _banco


def qual_backend():
    return "Supabase" if isinstance(banco(), BancoSupabase) else "SQLite local"
