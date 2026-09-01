# LapkWeb

Aplicação web em **Flask** para monitorar atualizações de jogos. Os jogos são cadastrados **manualmente** (nome, URL e versão local), e o sistema faz a **verificação automática** da versão publicada na página de origem, sinalizando quando existe uma atualização disponível.

## Sobre o projeto

O LapkWeb resolve um problema simples: acompanhar se os jogos que você já baixou/instalou receberam uma nova versão, sem precisar visitar manualmente cada página de tempos em tempos.

Fluxo de uso:
1. Você adiciona um jogo informando nome, URL da página e a versão que você já possui localmente.
2. A aplicação acessa a URL, extrai o texto da página e procura por campos como **"Versão do jogo:"** e **"Atualizado em:"**.
3. Se a versão encontrada na página for diferente da versão local salva, o jogo é marcado como **pendente de atualização** no painel.
4. Quando você atualizar o jogo, basta marcar como atualizado para sincronizar a versão local com a versão do site.

## Funcionalidades

- Cadastro manual de jogos (nome, URL, versão local)
- Verificação individual ou em lote ("verificar todos") da versão mais recente
- Extração automática de versão e data de atualização via scraping (regex + BeautifulSoup)
- Indicação visual de jogos com atualização pendente
- Edição e exclusão de jogos cadastrados
- Marcar jogo como atualizado (sincroniza versão local com a versão do site)
- Registro da data/hora da última verificação e de eventuais erros de acesso à página

## Tecnologias utilizadas

- [Python 3](https://www.python.org/)
- [Flask](https://flask.palletsprojects.com/) — framework web e roteamento
- [Requests](https://docs.python-requests.org/) — requisições HTTP
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — parsing HTML
- Armazenamento simples em arquivo **JSON** (sem banco de dados)

## Estrutura do projeto

```
lapkweb/
├── app.py            # Ponto de entrada da aplicação Flask
├── config.py          # Configurações gerais (host, porta, timeouts, rótulos de busca)
├── routes.py          # Rotas HTTP (blueprint "jogos")
├── scraper.py          # Lógica de scraping e extração de versão
├── storage.py          # Persistência dos jogos em JSON (CRUD)
├── data/               # Arquivo jogos.json com os dados salvos
├── static/             # Arquivos estáticos (CSS/JS)
└── templates/           # Templates HTML (index, edição)
```

## Como funciona a verificação de versão

O `scraper.py` faz uma requisição à URL cadastrada, extrai todo o texto da página e usa expressões regulares para localizar o valor logo após o rótulo configurado em `LABEL_VERSAO` (por padrão, **"versão do jogo"**) e `LABEL_ATUALIZADO_EM` (**"atualizado em"**), parando a captura ao encontrar outros rótulos conhecidos da página (tradução, idioma, plataforma, desenvolvedor etc.), definidos em `STOP_LABELS`.

Se o rótulo de versão não for encontrado, ou se a página não puder ser acessada, o erro é registrado no próprio jogo e exibido na interface.

## Modelo de dados

Cada jogo é representado pela dataclass `Jogo`, salva em `data/jogos.json`:

| Campo | Descrição |
|---|---|
| `id` | Identificador numérico |
| `nome` | Nome do jogo |
| `url` | URL da página monitorada |
| `versao_local` | Versão que você possui atualmente |
| `versao_site` | Última versão encontrada na página |
| `atualizado_em` | Data de atualização informada na página |
| `ultima_verificacao` | Data/hora da última checagem feita pela aplicação |
| `erro` | Mensagem de erro, caso a verificação falhe |

## Rotas principais

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Lista os jogos cadastrados e o resumo de pendências |
| `/adicionar` | POST | Adiciona um novo jogo |
| `/editar/<id>` | GET/POST | Exibe/salva a edição de um jogo |
| `/verificar/<id>` | POST | Verifica a versão de um jogo específico |
| `/verificar-todos` | POST | Verifica a versão de todos os jogos cadastrados |
| `/marcar-atualizado/<id>` | POST | Sincroniza a versão local com a versão do site |
| `/excluir/<id>` | POST | Remove um jogo cadastrado |

## Instalação e uso

Pré-requisitos: Python 3 instalado.

```bash
# Clonar o repositório
git clone https://github.com/phoenixsrd/lapkweb.git
cd lapkweb

# Instalar as dependências
pip install -r requirements.txt

# Rodar a aplicação
python app.py
```

Por padrão, a aplicação sobe em `http://0.0.0.0:5000`.

## Configuração

As principais opções podem ser ajustadas em `config.py`:

- `HOST` / `PORT` / `DEBUG` — parâmetros do servidor Flask
- `DATA_FILE` — caminho do arquivo JSON de persistência
- `REQUEST_HEADERS` / `REQUEST_TIMEOUT` — configuração das requisições de scraping
- `LABEL_VERSAO` / `LABEL_ATUALIZADO_EM` / `STOP_LABELS` — rótulos usados para localizar as informações na página

## Observações

- Não há autenticação: a aplicação foi pensada para uso pessoal/local.
- O scraping depende do formato de texto da página de origem; mudanças no layout do site monitorado podem exigir ajuste dos rótulos em `config.py`.