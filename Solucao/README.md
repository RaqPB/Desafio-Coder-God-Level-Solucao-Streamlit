
# 🍽️ Plataforma Ingrediente Certo - Solução do Desafio Coder God Level do Nola

## 💡 Descrição do Projeto

A plataforma **Ingrediente Certo** é um **ambiente de analytics customizável** projetada para **donos e gerentes de restaurantes**. Com o objetivo de ser **simples** e **intuitiva**, ela transforma dados operacionais complexos (PostgreSQL, 500k+ registros) em **informações práticas**.

O **Ingrediente Certo** permite que o usuário utilize seus dados para **diagnosticar problemas** operacionais e financeiros (como queda no ticket médio, baixa margem ou lentidão na entrega) e **tomar decisões estratégicas** em minutos, sem precisar de conhecimento técnico.

## ⚙️ Setup Técnico e Execução Rápida
Após clonar o repositório navegue para a pasta raiz do projeto (Plataforma Ingrediente Certo): 
### 1. Preparação do ambiente
    ```bash
        # 1. Instale o ambiente virtual (opcional, mas recomendado)
        python -m venv venv
        source venv/bin/activate  # Windows: .\venv\Scripts\activate

        # 2. Instale as bibliotecas Python (a partir do arquivo requirements.txt)
        pip install -r requirements.txt 
    ```

### 1.2 Configuração das Credenciais do Banco (.streamlit/secrets.toml)

O Streamlit exige que as credenciais do banco de dados sejam armazenadas em um arquivo seguro. Crie o diretório .streamlit/ na raiz do projeto e, dentro dele, o arquivo secrets.toml com o seguinte formato:
    
```bash
        #secrets.toml
        [connections.postgres]
        host = "localhost" # O nome do serviço Docker do PostgreSQL (ou localhost, dependendo do setup)
        database = "challenge_db"
        user = "challenge"
        password = "challenge_password"
        port = 5432
```

OBS: As credenciais acima são as padrão definidas nos arquivos de configuração Docker.

### 2. Ativar e Popular o Banco de Dados (Docker)
**ATENÇÃO**: *Caso seja a primeira vez que esteja acessando é necessário rodar os arquivos da pasta docker. Pois a solução depende dos arquivos gerados dessa pasta. Se os dados já tiverem sido gerados verifique se o conteiner está ativado.*

*OBS: Caso o Docker esteja ativo mas não esteja conectando conectando verifique se as credenciais estão corretas no arquivo secrets.toml.* 

```bash
        cd docker

        docker compose down -v 2>/dev/null || true
        docker compose build --no-cache data-generator
        docker compose up -d postgres
        docker compose run --rm data-generator
        docker compose --profile tools up -d pgadmin
```
Caso queira verificar se os dados foram gerados use esse comando

```bash

    docker compose exec postgres psql -U challenge challenge_db -c 'SELECT COUNT(*) FROM sales;'
```
### 3. Executar a aplicação
Com o banco ativo e populado, inicie a plataforma Ingrediente Certo:

```bash
        streamlit run Homepage.py
```
A aplicação será aberta automaticamente no seu navegador