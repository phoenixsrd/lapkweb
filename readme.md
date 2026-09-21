# 🎮 LapkWeb

O **LapkWeb** é uma aplicação Flask para acompanhar atualizações de jogos. Você cadastra manualmente o nome, a URL da página e a versão instalada; o sistema acessa a página, extrai a versão publicada e indica no painel quando existe uma atualização pendente.

## Fluxo de uso

1. Cadastre um jogo com nome, URL e versão local.
2. Use a verificação individual ou **Verificar todos**.
3. O scraper baixa o HTML, transforma a página em texto e procura os rótulos configurados para versão e data.
4. Se a versão do site for diferente da versão local, o jogo aparece como pendente.
5. Depois de atualizar o jogo, use **Marcar como atualizado** para sincronizar a versão local.

```text
formulário → storage JSON → scraper requests/BeautifulSoup → comparação → painel Flask
```

## Funcionalidades

- Cadastro, edição e exclusão de jogos.
- Verificação individual ou em lote.
- Extração por regex com `BeautifulSoup`.
- Indicação visual de atualizações disponíveis.
- Registro de versão publicada, data da página, última verificação e erros.
- Persistência simples em `data/jogos.json`, sem banco de dados.
- Interface HTML/CSS servida pelos templates Flask.

## Estrutura

```text
app.py        # Cria a aplicação Flask e registra o blueprint
config.py     # Host, porta, timeout, headers e rótulos do scraper
routes.py     # Rotas de cadastro, edição, verificação e exclusão
scraper.py    # Requisição HTTP e extração de versão/data
storage.py    # Modelo Jogo e operações CRUD no JSON
data/         # Dados persistidos localmente
static/       # CSS e arquivos estáticos
templates/    # Páginas index e edição
```

As rotas principais são `/`, `/adicionar`, `/editar/<id>`, `/verificar/<id>`, `/verificar-todos`, `/marcar-atualizado/<id>` e `/excluir/<id>`.

## Instalação e execução

```bash
git clone https://github.com/phoenixsrd/lapkweb.git
cd lapkweb
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\\Scripts\\activate        # Windows
pip install -r requirements.txt
python app.py
```

Acesse `http://127.0.0.1:5000` ou o endereço configurado em `config.py`.

## Configuração do scraper

A aplicação procura rótulos como `Versão do jogo:` e `Atualizado em:`. Ajuste em `config.py`:

- `HOST`, `PORT` e `DEBUG`.
- `DATA_FILE` para o arquivo de persistência.
- `REQUEST_HEADERS` e `REQUEST_TIMEOUT`.
- `LABEL_VERSAO`, `LABEL_ATUALIZADO_EM` e `STOP_LABELS`.

O site monitorado precisa deixar essas informações disponíveis no HTML retornado pela requisição. Se a página depender de JavaScript para montar o conteúdo, o `requests` não executará esse JavaScript e será necessário adaptar a estratégia.

## Limitações e segurança

O projeto foi pensado para uso pessoal/local e não possui autenticação. Proteja o acesso se for publicado na internet. O scraping depende do formato textual das páginas monitoradas: mudanças de layout ou de rótulos podem exigir alterações em `config.py` ou `scraper.py`.
