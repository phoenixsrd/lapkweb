# LapkWeb

Aplicação web em **Flask** para monitorar atualizações de jogos. Os jogos são cadastrados **manualmente** (nome, URL e versão local), e o sistema verifica a versão publicada na página de origem, sinalizando quando existe uma atualização disponível.

## Sobre o projeto

O LapkWeb resolve um problema simples: acompanhar se os jogos que você já baixou/instalou receberam uma nova versão, sem precisar visitar manualmente cada página de tempos em tempos.

Fluxo de uso:
1. Você adiciona um jogo informando nome, URL da página e a versão que você já possui localmente. A aplicação já faz a primeira verificação na hora.
2. A aplicação acessa a URL, extrai o texto da página e procura por campos como **"Versão do jogo:"** e **"Data da Atualização:"**.
3. Se a versão encontrada na página for diferente da versão local, o jogo é marcado como **pendente de atualização** e sobe para o topo da lista.
4. Quando você atualizar o jogo, basta marcar como atualizado para sincronizar a versão local com a versão do site.

## Funcionalidades

- Cadastro manual de jogos (nome, URL, versão local), com validação e bloqueio de URLs duplicadas
- Verificação individual ou em lote ("verificar todos"); o lote roda em paralelo
- Extração de versão e data de atualização via scraping, ignorando acentos e maiúsculas nos rótulos
- Lista ordenada por prioridade (com atualização → com erro → não verificado → em dia)
- Busca por nome e filtros (Todos / Atualizações / Erros) direto no navegador
- Link para a página de cada jogo e botão **Abrir página** quando há atualização
- Avisos na tela após cada ação e botões com estado de "verificando…"
- Registro de quando a última verificação aconteceu e de quando a novidade foi detectada
- Falha temporária de rede **não apaga** o que já se sabia sobre a versão do site
- Edição, exclusão (com confirmação) e "marcar atualizado"
- Verificação automática periódica em segundo plano (opcional, desligada por padrão)
- Proteção CSRF nos formulários e gravação atômica do arquivo de dados

## Tecnologias utilizadas

- [Python 3](https://www.python.org/) (3.9 ou superior; testado no 3.12)
- [Flask](https://flask.palletsprojects.com/) — framework web e roteamento
- [Requests](https://docs.python-requests.org/) — requisições HTTP (com novas tentativas automáticas)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — parsing HTML
- Armazenamento simples em arquivo **JSON** (sem banco de dados)
- Um pouco de JavaScript puro (sem dependências) para busca, filtros e confirmações

## Estrutura do projeto

```
lapkweb/
├── app.py            # Ponto de entrada (cria o app, migra dados, liga o agendador)
├── config.py         # Configurações (servidor, requisições, rótulos de busca)
├── routes.py         # Rotas HTTP (blueprint "jogos") e validação dos formulários
├── servico.py        # Regra de negócio da verificação (usada pelas rotas e pelo agendador)
├── scraper.py        # Download da página e extração de versão/data
├── versoes.py        # Funções puras: normalização, comparação e extração de campos
├── storage.py        # Persistência em JSON (CRUD, trava, escrita atômica, migração)
├── tempo.py          # Datas em ISO 8601 e formatação ("há 5 min")
├── seguranca.py      # Chave secreta persistente e proteção CSRF
├── agendador.py      # Verificação periódica em segundo plano (opcional)
├── erros.py          # Páginas de erro e filtros de template
├── data/             # jogos.json (seus dados) e .secret_key (gerada sozinha)
├── static/           # style.css, app.js, favicon.svg
├── templates/        # base, index, edit, erro
└── tests/            # testes automatizados (unittest)
```

## Como funciona a verificação de versão

O `scraper.py` baixa a URL cadastrada (com timeout, novas tentativas em erros 5xx e limite de tamanho), remove scripts/estilos e extrai o texto da página. Depois procura o valor logo após o rótulo configurado:

- **Versão:** `LABELS_VERSAO` (por padrão `versão do jogo`, `versão atual`, `game version`)
- **Data:** `LABELS_DATA` (por padrão `data da atualização`, `atualizado em`, `última atualização`)

A captura termina ao encontrar qualquer outro rótulo conhecido (`STOP_LABELS`, mais os rótulos de versão e data). Acentos e maiúsculas não importam. Quando só a data aparece colada na versão (`0.2.9b + DLC Data da Atualização: 08/08/2026`), os dois são separados automaticamente.

A comparação ignora diferenças de maiúsculas, espaços e um "v" inicial (`v0.95` = `0.95`). A **data não entra na comparação**: só a versão decide se há atualização; a data é exibida como "publicado em".

Se o rótulo de versão não for encontrado, se o valor capturado ficar longo demais (sinal de que falta um rótulo de parada em `STOP_LABELS`) ou se a página não puder ser acessada, o erro é registrado no jogo e exibido no card, com uma mensagem específica (timeout, HTTP 403/404, conexão etc.).

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
| `ultima_verificacao` | Data/hora (ISO 8601) da última checagem |
| `detectado_em` | Quando a novidade pendente foi detectada pela primeira vez |
| `erro` | Mensagem de erro da última verificação, se houver |

### Migração automática

Arquivos do formato antigo (data embutida em `versao_local`/`versao_site`, horário no formato `dd/mm HH:MM`) são convertidos na primeira execução. Antes de qualquer alteração, a aplicação salva uma cópia do original como `data/jogos.json.bak-AAAAMMDD-HHMMSS`.

Se o `jogos.json` estiver corrompido, a aplicação **não sobrescreve** nada: a página mostra o problema e o arquivo fica como está para você corrigir.

## Rotas principais

Todas as rotas `POST` exigem o token CSRF (os formulários da interface já o enviam).

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Lista os jogos cadastrados e o resumo de pendências |
| `/adicionar` | POST | Valida, adiciona e já verifica um novo jogo |
| `/editar/<id>` | GET/POST | Exibe/salva a edição de um jogo |
| `/verificar/<id>` | POST | Verifica a versão de um jogo específico |
| `/verificar-todos` | POST | Verifica todos os jogos (em paralelo) |
| `/marcar-atualizado/<id>` | POST | Sincroniza a versão local com a versão do site |
| `/excluir/<id>` | POST | Remove um jogo cadastrado |

## Instalação e uso

Pré-requisitos: Python 3.9+ instalado.

```bash
# Clonar o repositório
git clone https://github.com/phoenixsrd/lapkweb.git
cd lapkweb

# (opcional) criar um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate

# Instalar as dependências
pip install -r requirements.txt

# Rodar a aplicação
python app.py
```

Por padrão, a aplicação sobe em `http://0.0.0.0:5000` (acessível por outros aparelhos da mesma rede, como o celular, pelo IP do computador).

## Configuração

Variáveis de ambiente (todas opcionais):

| Variável | Padrão | Descrição |
|---|---|---|
| `LAPKWEB_HOST` | `0.0.0.0` | Endereço do servidor. Use `127.0.0.1` para aceitar só acessos da própria máquina |
| `LAPKWEB_PORT` | `5000` | Porta |
| `LAPKWEB_DEBUG` | `false` | Modo debug do Flask |
| `LAPKWEB_DATA_DIR` | `./data` | Pasta do `jogos.json` e da chave secreta |
| `LAPKWEB_SECRET_KEY` | gerada e salva em `data/.secret_key` | Chave das sessões/CSRF |
| `LAPKWEB_VERIFICAR_A_CADA_HORAS` | `0` | Intervalo da verificação automática em horas (`0` desliga; aceita decimais, ex.: `0.5`) |

Exemplo: verificar sozinho a cada 6 horas:

```bash
LAPKWEB_VERIFICAR_A_CADA_HORAS=6 python app.py
```

A primeira verificação automática acontece alguns segundos depois de o servidor subir e as seguintes seguem o intervalo definido.

Opções de scraping ficam em `config.py`: `REQUEST_HEADERS`, `REQUEST_TIMEOUT`, `REQUEST_RETRIES`, `MAX_WORKERS`, `MAX_BYTES`, `LABELS_VERSAO`, `LABELS_DATA` e `STOP_LABELS`.

## Testes

Os testes usam apenas a biblioteca padrão (`unittest`) e uma pasta temporária, então **nunca mexem nos seus dados**:

```bash
python -m unittest discover -s tests -t .
```

Cobrem a extração de versão/data, o scraper (incluindo um servidor HTTP local para testar erros e novas tentativas), o armazenamento e a migração, a regra de verificação e as rotas (CSRF, validação, duplicidade etc.).

## Observações

- Não há login: a aplicação foi pensada para uso pessoal/local. Os formulários têm proteção CSRF, mas, se for expor a aplicação além da sua rede, coloque-a atrás de um proxy com autenticação.
- Rode **um único processo** (a trava que protege o `jogos.json` vale dentro do mesmo processo). O servidor embutido do Flask serve para uso pessoal.
- Mantenha `data/.secret_key` fora do Git (já está no `.gitignore`).
- O scraping depende do formato de texto da página de origem; mudanças no layout do site monitorado podem exigir ajuste dos rótulos em `config.py`.
