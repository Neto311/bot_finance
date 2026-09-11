# 💰 Bot Finance — Assistente financeiro via Telegram

Assistente para registrar gastos por texto ou mensagem de voz no Telegram, usando Groq para extrair os dados e Minhas Economias para criar, editar e excluir transações. A API FastAPI mantém um registro local por usuário, com saldo, histórico e resumos mensais.

**Estado atual:** MVP em desenvolvimento. O cadastro aceita somente `GASTO`, exige usuário previamente autorizado e conexão com Minhas Economias. O saldo e os relatórios exibidos pelo bot são calculados no banco local; não representam uma sincronização completa da conta externa.

## Funcionalidades implementadas

- Registro de gastos em linguagem natural, por exemplo: “Gastei 50 reais com pizza hoje”.
- Transcrição de voz com `whisper-large-v3-turbo` e extração estruturada com `openai/gpt-oss-120b`, ambos via Groq.
- Consulta ao catálogo de categorias e subcategorias do Minhas Economias durante a criação.
- Criação externa seguida de persistência local com `referencia_externa`.
- Listagem, consulta por mês/ano, resumo por categoria e ajuste manual do saldo local.
- Edição de valor, descrição e categoria, e exclusão usando a referência externa.
- Isolamento por usuário e numeração individual das transações (`numero_usuario`).
- Identidades externas associadas a usuários ativos e autenticação entre bot e API por Bearer token.
- OAuth com PKCE S256, `state` de uso único e validade de 10 minutos.
- Tokens OAuth por usuário, criptografados com Fernet no banco; renovação quando faltam até dois minutos para expirar.
- Docker Compose para desenvolvimento e produção, PostgreSQL, migrações Alembic e HTTPS com Caddy.
- Deploy de produção pelo GitHub Actions via AWS Systems Manager (SSM).

Existe também uma implementação de WhatsApp/Twilio, mas ela ainda precisa ser adaptada ao contrato atual de autenticação e identidade da API.

## Arquitetura

```mermaid
flowchart LR
    U[Usuário] --> T[Bot Telegram]
    T -->|HTTP + Bearer + identidade| A[API FastAPI]
    A --> G[Groq: texto e voz]
    A --> F[FinanceService]
    F --> P[MinhasEconomiasProvider]
    P -->|MCP / JSON-RPC / SSE| M[Minhas Economias]
    A --> D[(PostgreSQL)]
    A --> O[OAuth com PKCE]
    O --> M
    O --> D
```

O Telegram roda em processo separado, por polling. A API resolve a identidade, consulta as categorias externas, interpreta a mensagem, executa a operação no Minhas Economias e atualiza o banco local. Consultas de histórico, saldo e resumo leem o banco local.

| Caminho | Responsabilidade |
| --- | --- |
| [main.py](main.py) | Aplicação FastAPI, roteadores e health check |
| [routes/](routes/) | Operações financeiras e conexão OAuth |
| [dependencies/](dependencies/) | Autenticação de serviço e resolução da identidade |
| [services/](services/) | Bot, Groq, regras financeiras, OAuth e criptografia |
| [providers/](providers/) | Contrato financeiro e implementação Minhas Economias |
| [integrations/minhaseconomias/](integrations/minhaseconomias/) | Cliente MCP/SSE e caches em memória |
| [models/](models/), [schemas/](schemas/), [repositories/](repositories/) | Persistência, contratos da API e acesso a dados |
| [migrations/](migrations/) | Evolução do banco com Alembic |
| [scripts/migrar_tokens_minhas_economias.py](scripts/migrar_tokens_minhas_economias.py) | Conversão de tokens legados para Fernet |
| [.github/workflows/deploy-prod.yml](.github/workflows/deploy-prod.yml) | Deploy na AWS |

### Tecnologias

Python **3.14+**, FastAPI, SQLAlchemy 2, PostgreSQL 17, Alembic, Pydantic, HTTPX, python-telegram-bot, Groq, cryptography/Fernet, Poetry, Docker Compose e Caddy.

O [pyproject.toml](pyproject.toml) e o [poetry.lock](poetry.lock) são usados na construção da imagem. O `requirements.txt` está desatualizado em relação a eles: não inclui Alembic nem cryptography e fixa `uvloop`, que não atende ao Windows nativo. Use Poetry ou Docker.

## Configuração

### Pré-requisitos

- Git; Docker com Compose para executar os containers.
- Para execução sem containers: Python 3.14+, Poetry 2.4.1 e PostgreSQL.
- Token do bot Telegram e chave da API Groq.
- Cliente OAuth do Minhas Economias com URI de redirecionamento configurada.
- Usuário ativo e identidade Telegram cadastrados no banco.
- Cartão chamado **Cartão Nubank** no Minhas Economias: esse nome está fixado em `FinanceService.preparar_transacao`. A descoberta procura cartões nas até 100 transações retornadas pelo provedor, portanto o cartão precisa aparecer nesse conjunto.

```bash
git clone https://github.com/Neto311/bot_finance.git
cd bot_finance
```

### Variáveis de ambiente

Use [.env.dev.example](.env.dev.example) ou [.env.prod.example](.env.prod.example) como base. Os arquivos reais `.env`, `.env.dev` e `.env.prod` são ignorados pelo Git.

| Variável | Uso |
| --- | --- |
| `APP_ENV` | `development` ou `production`; em produção, exige URL de banco |
| `DATABASE_URL` | Conexão SQLAlchemy com PostgreSQL; `DATA_BASE` é um alias legado |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Inicialização do PostgreSQL nos Compose |
| `GROQ` | Chave usada pela API para texto e áudio |
| `TELEGRAM` | Token lido pelo bot |
| `TELEGRAM_DEV` | Token que o Compose de desenvolvimento repassa como `TELEGRAM` |
| `API_URL` | Endereço da API visto pelo bot; configure explicitamente na execução local |
| `INTERNAL_API_KEY` | Segredo compartilhado entre API e bot; obrigatório para rotas protegidas |
| `TOKEN_ENCRYPTION_KEY` | Chave Fernet para persistir e ler tokens OAuth |
| `MINHAS_ECONOMIAS_CLIENT_ID` | Identificador do cliente OAuth |
| `MINHAS_ECONOMIAS_REDIRECT_URI` | URI completa da rota de callback |
| `MINHAS_ECONOMIAS_MCP_URL` | Presente nos exemplos, mas o cliente atual usa a URL fixa no código |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | Credenciais da integração WhatsApp ainda incompleta |
| `IMAGE_TAG` | Tag opcional da imagem Docker; padrão `local` |

Gere os segredos no seu ambiente Python com as dependências instaladas:

```bash
poetry run python -c "import secrets; print(secrets.token_urlsafe(32))"
poetry run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use o primeiro resultado como `INTERNAL_API_KEY` e o segundo como `TOKEN_ENCRYPTION_KEY`. Guarde a chave Fernet junto da estratégia de backup: trocar ou perder essa chave impede a leitura dos tokens existentes.

**Ajuste necessário nos exemplos atuais:** adicione `INTERNAL_API_KEY` ao arquivo de ambiente escolhido. O Compose de produção já a repassa para API e bot; o de desenvolvimento ainda não. No `compose.dev.yaml`, adicione a entrada abaixo ao bloco `environment` de **api-dev e bot-dev** antes de subir esses serviços:

```yaml
INTERNAL_API_KEY: ${INTERNAL_API_KEY:?INTERNAL_API_KEY obrigatoria}
```

### Desenvolvimento com Docker

Copie `.env.dev.example` para `.env.dev` e preencha as variáveis e o ajuste acima. No PowerShell:

```powershell
Copy-Item .env.dev.example .env.dev
```

No Linux/macOS, use `cp .env.dev.example .env.dev`.

```bash
docker compose --env-file .env.dev -f compose.dev.yaml up -d --build
docker compose --env-file .env.dev -f compose.dev.yaml --profile bot up -d --build
docker compose --env-file .env.dev -f compose.dev.yaml ps
```

O primeiro comando inicia banco, migrações e API. O segundo inclui o bot opcional; use um token de desenvolvimento separado.

- API: `http://127.0.0.1:8001`.
- Swagger: `http://127.0.0.1:8001/docs`.
- PostgreSQL no host: `127.0.0.1:5433`; entre containers: `db-dev:5432`.
- Dados persistidos no volume `postgres_dev_data`.

### Execução local com Poetry

```bash
poetry install --no-root
```

Crie um `.env` na raiz com as variáveis da tabela. Aponte `DATABASE_URL` para o PostgreSQL acessível pelo host, por exemplo `postgresql+psycopg2://USUARIO:SENHA@127.0.0.1:5433/BANCO`, e defina `API_URL=http://127.0.0.1:8000` e `TELEGRAM`.

```bash
poetry run alembic upgrade head
poetry run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Em outro terminal, na raiz do projeto:

```bash
poetry run python services/bot_telegram.py
```

Embora `database.py` tenha fallback para SQLite (`test.db`) em desenvolvimento, as migrações atuais contêm operações específicas de PostgreSQL. Utilize PostgreSQL para reproduzir o esquema completo.

## Primeiro acesso e uso do Telegram

1. Envie `/meuid` ao bot para obter seu identificador Telegram.
2. Cadastre administrativamente um registro em `usuarios` e outro em `identidades_externas`. Não há endpoint público de cadastro.
3. Envie `/conectar_minhas_economias`, abra o link e conclua o OAuth.
4. Envie `/start` para abrir o teclado ou mande um texto/áudio de gasto.

Exemplo para um **novo usuário**, executado em um console Python na raiz com o ambiente do banco correto:

```python
from database import SessionLocal
from models.financas import IdentidadeExterna, Usuario

with SessionLocal.begin() as db:
    usuario = Usuario(nome="Seu nome", ativo=True, saldo=0.0)
    db.add(usuario)
    db.flush()
    db.add(IdentidadeExterna(
        usuario_id=usuario.id,
        provedor="telegram",
        identificador_externo="SEU_ID_TELEGRAM",
    ))
```

Substitua os valores e execute uma vez por identidade. Se o usuário já existir, associe a identidade ao seu `usuario_id` existente.

| Comando | Ação |
| --- | --- |
| `/start` | Abre o menu de ações |
| `/meuid` | Mostra o identificador Telegram |
| `/conectar_minhas_economias` | Gera o link de autorização OAuth |
| `/desconectar_minhas_economias` | Remove tokens do banco e cache local |
| `/ver_itens` | Lista as transações locais do usuário |
| `/ver_saldo` | Consulta o saldo local |
| `/atualizar_saldo 1000.50` | Define manualmente o saldo local; use ponto decimal |
| `/resumo 09 2026` | Soma os valores locais do mês e agrupa por categoria |
| `/ver_transacao_data 09 2026` | Lista transações do mês |
| `/deletar_transacao 12` | Exclui a transação externa e depois a local |
| `/atualizar_transacao 12 pizza 45 reais` | Reinterpreta o texto e edita a transação |

O ID exibido pelo Telegram é `numero_usuario`, não a chave primária global do banco. A desconexão remove as credenciais locais; não há chamada de revogação no provedor.

## API HTTP

As rotas financeiras e de gerenciamento OAuth exigem:

```http
Authorization: Bearer SUA_INTERNAL_API_KEY
```

Para consultas, edição, exclusão, saldo e gerenciamento OAuth, envie também:

```http
X-Identity-Provider: telegram
X-External-Identity: SEU_ID_TELEGRAM
```

Na criação por texto, a identidade vai no JSON; por áudio, nos campos multipart.

| Método | Rota | Entrada / finalidade |
| --- | --- | --- |
| GET | `/` | Health check público: `{"status":"ok"}` |
| POST | `/financas` | JSON com `texto`, `provedor`, `identificador_externo` |
| POST | `/financas/audio` | Multipart com `file`, `provedor`, `identificador_externo` |
| GET | `/financas` | Lista local do usuário |
| PUT | `/financas/{numero_usuario}` | JSON com `texto` |
| DELETE | `/financas/{numero_usuario}` | Exclui usando a referência externa |
| GET | `/financas/data?mes=9&ano=2026` | Consulta local por período |
| GET / PUT | `/saldo` | Consulta ou define saldo; PUT recebe `{"saldo":1000.50}` |
| GET | `/resumo?mes=9&ano=2026` | Total e categorias do mês |
| POST | `/integracoes/minhas-economias/conectar` | Retorna `url_autorizacao` |
| GET | `/integracoes/minhas-economias/callback` | Callback público com `code` e `state` |
| GET | `/integracoes/minhas-economias/status` | Presença e expiração das credenciais locais |
| DELETE | `/integracoes/minhas-economias/conexao` | Remove a conexão local |
| POST | `/whatsapp` | Webhook legado, ainda incompatível com o fluxo autenticado |

Exemplo de corpo para registrar um gasto:

```json
{
  "texto": "Gastei 50 reais com pizza hoje",
  "provedor": "telegram",
  "identificador_externo": "SEU_ID_TELEGRAM"
}
```

O health check confirma que a API responde; não testa Groq, OAuth, MCP ou a disponibilidade do banco. O endpoint de status OAuth indica credenciais armazenadas, sem validar a conexão com o provedor.

## Banco de dados e tokens legados

O esquema contém `usuarios`, `identidades_externas`, `financas` e `minhas_economias_token`. As seis revisões Alembic criam as tabelas e acrescentam identidade externa, proprietário, referência externa, numeração por usuário e associação dos tokens ao usuário.

```bash
poetry run alembic current
poetry run alembic upgrade head
```

Em bases antigas, revise os vínculos antes de migrar: há migrações que atribuem transações ao usuário `1` e convertem tokens de `usuario_local` para esse mesmo usuário. Outros registros legados podem precisar de tratamento administrativo.

Para tokens antigos em texto puro, faça backup do banco, configure a chave Fernet correta e execute:

```bash
poetry run python -m scripts.migrar_tokens_minhas_economias
```

O script converte campos sem o prefixo `fernet:v1:` e informa a quantidade de registros alterados. A aplicação atual rejeita tokens sem esse formato. O script não faz rotação de chave e não valida criptograficamente os campos que já possuem o prefixo.

## Produção e deploy

Copie `.env.prod.example` para `.env.prod`, preencha os segredos, incluindo `INTERNAL_API_KEY`, e ajuste o domínio no [Caddyfile](Caddyfile) e na URI de callback.

```bash
docker compose --env-file .env.prod -f compose.prod.yaml config --quiet
docker compose --env-file .env.prod -f compose.prod.yaml up -d --build
docker compose --env-file .env.prod -f compose.prod.yaml ps
```

O ambiente inclui PostgreSQL, migração, API, bot e Caddy. O banco não publica porta no host; a API fica em `127.0.0.1:8000`. O Caddy publica 80/443 e encaminha somente as rotas de conexão e callback OAuth; as demais URLs públicas retornam 404. O Swagger deve ser acessado localmente ou por túnel.

O workflow [Deploy production](.github/workflows/deploy-prod.yml) roda em pushes para `main` ou por disparo manual. Ele assume uma role AWS via OIDC, executa o deploy por SSM, aplica migrações, recria os serviços e verifica a API e as respostas públicas. Conta, role, instância, domínio e diretório `/opt/bot-finance/app` estão definidos para a instalação atual e precisam ser adaptados em outro ambiente. A instância precisa ter o repositório, Docker/Compose, acesso SSM e `.env.prod` configurados.

## Limitações e próximos ajustes

- **Receitas:** a criação rejeita `GANHO` com HTTP 422. O resumo soma todos os registros do período sem filtrar o tipo; isso merece ajuste caso existam receitas legadas.
- **Cartão fixo:** seleção de “Cartão Nubank” depende das transações retornadas pelo provedor; ainda não há escolha de cartão por usuário.
- **Consistência externa/local:** operações externas e commits locais não formam uma transação atômica. Não há mecanismo de reconciliação ou sincronização das alterações feitas diretamente no Minhas Economias.
- **Edição parcial:** a edição local altera valor, categoria e descrição, sem mudar data ou tipo. A extração na edição ainda não recebe o catálogo de categorias.
- **Registros antigos:** editar ou excluir transações sem referência externa retorna HTTP 409.
- **Escala:** tentativas OAuth e cache de tokens vivem na memória do processo. Mantenha uma instância da API com um worker para o fluxo atual; reiniciar invalida autorizações pendentes.
- **WhatsApp:** faltam envio de Bearer/identidade ao backend e validação de assinatura Twilio; a rota não está exposta pelo Caddy atual.
- **Configuração:** falta `INTERNAL_API_KEY` nos exemplos e seu repasse no Compose de desenvolvimento; a URL MCP está fixa no cliente.
- **Qualidade:** não há suíte de testes automatizados versionada nem etapa de testes no workflow atual.

Esta documentação descreve o código e a infraestrutura versionados; a execução completa depende das credenciais e dos serviços externos configurados.
