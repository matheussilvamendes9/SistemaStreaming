# StreamHub — Sistema de Gerenciamento de Streaming

O **StreamHub** é um sistema acadêmico de gerenciamento de uma plataforma de streaming, desenvolvido em Python com Streamlit e MySQL. A aplicação possui funcionalidades administrativas para gerenciar usuários, catálogo de conteúdos, assinaturas e histórico de reprodução, além de um módulo de análise de dados baseado em informações públicas do IMDb.

O projeto utiliza dois bancos de dados com finalidades distintas: um banco operacional, responsável pelas informações do sistema, e um banco analítico, utilizado para explorar dados do mercado audiovisual.

## Funcionalidades

### Banco operacional — StreamHub

- **Visão geral:** apresentação de indicadores do sistema.
- **Usuários:** cadastro, consulta e exclusão de usuários.
- **Catálogo:** gerenciamento de filmes, séries, gêneros e episódios.
- **Assinaturas:** gerenciamento de planos e assinaturas.
- **Histórico:** consulta dos registros de reprodução.
- **Indicadores:** acompanhamento de informações como quantidade de usuários, conteúdos, reproduções e assinaturas ativas.

### Banco analítico — IMDb

O módulo de análise utiliza dados públicos disponibilizados pelo IMDb para apresentar informações sobre produções audiovisuais.

Entre as análises disponíveis estão:

- Indicadores gerais dos dados importados.
- Comparação entre tipos de produção.
- Distribuição das notas dos títulos.
- Evolução da quantidade de produções ao longo dos anos.
- Análise da duração média das produções.
- Ranking de filmes por gênero, considerando um mínimo de votos.

## Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal |
| Streamlit | Interface web |
| MySQL | Armazenamento dos dados |
| mysql-connector-python | Conexão com o MySQL |
| Pandas | Manipulação de dados |
| Altair | Visualização de dados |
| python-dotenv | Gerenciamento de variáveis de ambiente |
| IMDb Datasets | Fonte dos dados analíticos |

## Organização do projeto

A aplicação está organizada em componentes de interface, serviços e conexão com os bancos de dados.

```text
SistemaStreaming/
│
├── app.py
│
├── components/
│   ├── analise.py
│   ├── usuarios.py
│   ├── catalogo.py
│   ├── assinaturas.py
│   ├── historico.py
│   └── ...
│
├── services/
│   ├── usuario_service.py
│   ├── catalogo_service.py
│   ├── assinatura_service.py
│   ├── analise_service.py
│   └── ...
│
├── database/
│   ├── connection.py
│   ├── setup_analise.py
│   └── ...
│
├── .env
└── README.md
```

*Alguns arquivos e diretórios auxiliares foram omitidos para simplificar a visualização.*

## Como executar o projeto

### 1. Pré-requisitos

Antes de iniciar, é necessário ter instalado:

- Python 3.10 ou superior.
- MySQL Server.
- MySQL Workbench (opcional, mas recomendado para administrar os bancos).
- Git.

### 2. Clonar o repositório

Abra o terminal e execute:

```bash
git clone https://github.com/matheussilvamendes9/SistemaStreaming.git
```

Entre na pasta do projeto:

```bash
cd SistemaStreaming
```

### 3. Criar um ambiente virtual

Recomenda-se utilizar um ambiente virtual para instalar as dependências isoladamente.

No Windows:

```powershell
python -m venv venv
```

Ative o ambiente:

```powershell
.\venv\Scripts\Activate.ps1
```

Caso utilize o Prompt de Comando:

```cmd
venv\Scripts\activate
```

### 4. Instalar as dependências

Com o ambiente virtual ativado, instale as bibliotecas utilizadas:

```bash
pip install streamlit pandas altair mysql-connector-python python-dotenv
```

### 5. Configurar os bancos de dados

O projeto utiliza dois bancos de dados MySQL:

| Banco | Finalidade |
|---|---|
| `streaming_db` | Armazenamento das informações operacionais |
| `analise_db` | Armazenamento dos dados analíticos do IMDb |

Crie os bancos no MySQL:

```sql
CREATE DATABASE streaming_db;
CREATE DATABASE analise_db;
```

Em seguida, execute o script SQL de criação das tabelas do banco operacional, disponibilizado no diretório `database` do projeto.

O banco operacional precisa ter suas tabelas criadas antes de iniciar a aplicação.

### 6. Configurar as variáveis de ambiente

Na raiz do projeto, crie um arquivo chamado `.env`.

Configure os dados de conexão com a sua instalação do MySQL. Exemplo:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha

DB_STREAMING_NAME=streaming_db
DB_ANALISE_NAME=analise_db
```

Substitua `sua_senha` pela senha configurada no seu MySQL.

**Importante:** confira os nomes das variáveis utilizados em `database/connection.py` ou no arquivo `.env.example`, caso disponível. As variáveis do `.env` precisam corresponder exatamente às esperadas pelo código.

Não compartilhe o arquivo `.env` nem envie suas credenciais para o GitHub.

### 7. Importar os dados do IMDb (Banco Analítico)

O Banco A utiliza os conjuntos de dados públicos do IMDb, disponibilizados em:

https://datasets.imdbws.com/

Para realizar a importação, execute:

```bash
python database/setup_analise.py
```

O script realiza o download, a descompactação e a importação dos arquivos necessários para o banco analítico.

A carga inclui os conjuntos:

- `title.basics.tsv.gz`: informações gerais das produções audiovisuais.
- `title.ratings.tsv.gz`: notas médias e quantidade de votos dos títulos.

**Atenção:** essa etapa importa milhões de registros e pode levar algum tempo, dependendo da conexão com a internet e do computador utilizado. Execute a importação apenas uma vez em uma base vazia. Se os dados já estiverem carregados, não execute novamente sem verificar o comportamento do script.

### 8. Executar a aplicação

Após configurar o MySQL, criar as tabelas e instalar as dependências, inicie o Streamlit:

```bash
streamlit run app.py
```

A aplicação será aberta no navegador, normalmente no endereço:

```text
http://localhost:8501
```

Caso o navegador não abra automaticamente, copie o endereço apresentado no terminal.

## Arquitetura da aplicação

O projeto utiliza uma separação entre a interface, as regras de negócio e o acesso aos dados.

O fluxo principal é:

1. O usuário interage com a interface Streamlit.
2. Os componentes chamam as funções disponíveis na camada de serviços.
3. Os serviços executam as operações e consultas necessárias.
4. A camada de conexão estabelece a comunicação com o banco MySQL correspondente.
5. Os resultados retornam para os componentes.
6. A interface apresenta as informações em tabelas, indicadores e gráficos.

O banco operacional e o banco analítico são independentes entre si, mas são acessados pela mesma aplicação.

## Observações

- O projeto possui foco administrativo e acadêmico; não implementa reprodução de vídeos.
- O módulo de assinaturas realiza o gerenciamento dos registros, sem integração com gateways de pagamento.
- Os dados do IMDb são utilizados para análises do mercado audiovisual e não representam o comportamento dos usuários do StreamHub.
- O projeto não possui um sistema completo de autenticação e autorização de usuários.
- Para executar a aplicação em outro computador, é necessário configurar o MySQL, criar as tabelas, preencher o `.env` e importar os dados analíticos caso se deseje utilizar esse módulo.
