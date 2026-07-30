# D'Coratto — Gerador de Propostas

App que gera a proposta comercial em PDF, no formato aprovado, a partir de um
formulário. Usa o mesmo motor (ReportLab) do PDF original — o resultado é idêntico.

## O que tem nesta pasta

- `app.py` — a interface (formulário)
- `gerador.py` — o motor que monta o PDF
- `requirements.txt` — bibliotecas necessárias
- `assets/` — logo, fotos institucionais, diferenciais, parceiros e fontes (não apague)

## Como testar no seu computador (opcional)

1. Instale o Python 3.10+.
2. No terminal, dentro desta pasta:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Abre sozinho no navegador em `http://localhost:8501`.

## Como publicar para a equipe (Streamlit Community Cloud — grátis)

Você faz isso uma vez. Depois é só um link que todos acessam.

### Passo 1 — Conta no GitHub
- Crie uma conta em https://github.com (grátis), se ainda não tiver.
- Crie um repositório novo (ex.: `dcoratto-propostas`). Pode ser **privado**.

### Passo 2 — Suba os arquivos
- No repositório, clique em **Add file → Upload files**.
- Arraste **tudo desta pasta** (o `app.py`, o `gerador.py`, o `requirements.txt`
  e a pasta `assets` inteira). Confirme (**Commit changes**).

### Passo 3 — Publique no Streamlit
- Acesse https://share.streamlit.io e entre com a conta do GitHub.
- Clique em **New app**.
- Selecione o repositório `dcoratto-propostas`, branch `main`, arquivo `app.py`.
- Clique em **Deploy**. Em 1–2 minutos sai um link público
  (ex.: `https://dcoratto-propostas.streamlit.app`).

### Passo 4 — Use e compartilhe
- Esse link funciona no PC e no celular. Mande para a equipe.
- Para atualizar algo depois (texto fixo, foto institucional), basta trocar o
  arquivo no GitHub — o app se atualiza sozinho.

## O que muda por projeto (no formulário)

- Cliente, nº da proposta, validade, forma de pagamento
- Data: entra automática no dia em que gerar
- Ambientes: nome, descrição, valor à vista, valor 12x, 1 ou 2 fotos
- Arquiteto: sem parceiro (sem destaque) ou com parceiro (foto, nome, @ → destaque)

## O que é fixo (embutido no app)

Institucional, parque fabril, diferenciais, materiais, empresas parceiras,
clientes e embaixador. Para mudar, troque os arquivos em `assets/` ou o texto
em `gerador.py`.
