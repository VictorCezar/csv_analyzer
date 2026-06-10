# Agente de IA para Análise Modular de CSV

Este é um agente de inteligência artificial modular para análise de dados tabulares (arquivos CSV), construído com **Python 3.11**, **LangChain**, **LangGraph**, **Pandas**, **Ragas** e **Pytest**. 

A aplicação conta com uma interface de linha de comando (CLI) e uma interface web interativa (FastAPI/Uvicorn), que permitem fazer perguntas e extrair insights analíticos de arquivos CSV usando o LLM Llama 3 (via Groq API) com um fluxo automático de refinamento de código e validação humana (*Human-in-the-Loop*).

---

## 1. Visão Geral Técnica do Projeto

O fluxo de processamento do agente é orquestrado de forma modular utilizando uma máquina de estados baseada em **LangGraph** (`AgentState`):
1. **Leitura e Sumarização (`parse_csv`)**: Carrega o arquivo CSV usando Pandas e extrai metadados estruturais (schema, tipos e preview) para enriquecer o prompt do LLM.
2. **Tradução da Pergunta (`understand_query`)**: Traduz a pergunta do usuário em linguagem natural para um script Python em Pandas.
3. **Execução Segura (`extract_data`)**: Executa localmente o script gerado. Se ocorrer algum erro de execução do Pandas, o fluxo de controle retroalimenta o erro ao LLM para que ele gere uma correção.
4. **Redação do Rascunho (`draft_response`)**: O LLM redige uma resposta final baseada exclusivamente nos dados extraídos e no idioma original da pergunta.
5. **Validação Humana (`human_validation`)**: O LangGraph interrompe o fluxo (*interrupt*) e envia o código Pandas gerado, os dados obtidos e o rascunho de resposta para aprovação do usuário. Se rejeitado, o feedback do usuário é alimentado no LLM para iniciar um refinamento.

---

## 2. Configurando a API Key do Groq (.env)

Antes de rodar o projeto localmente, é necessário obter as credenciais da API do Groq.

1. **Criar a Groq API Key**:
   - Acesse o console oficial do Groq: [https://console.groq.com/](https://console.groq.com/).
   - Faça login ou crie uma conta gratuita.
   - Vá para a seção **API Keys** no painel lateral.
   - Clique em **Create API Key**, atribua um nome a ela e copie a chave gerada (com formato `gsk_...`).
2. **Configurar o Arquivo `.env`**:
   - Duplique o arquivo `.env.example` presente na raiz do projeto e renomeie a cópia para `.env`.
   - Adicione a chave gerada à variável `GROQ_API_KEY`:
     ```env
     GROQ_API_KEY=gsk_suachaveaqui...
     ```

---

## 3. Passo a Passo: Subir e Testar Localmente via Docker (Recomendado)

O uso do container Docker é a forma mais simples e rápida de empacotar e executar o agente sem conflito de dependências.

### Passo 1: Atualizar o Repositório Local
Sempre que fizer novas modificações ou realizar um `git pull`, certifique-se de estar com o código atualizado:
```bash
git pull origin main
```

### Passo 2: Construir a Imagem Docker
Na raiz do projeto (onde está localizado o `Dockerfile`), execute o comando para compilar a imagem:
```bash
docker build -t csv-ai-agent .
```

### Passo 3: Executar o Container

#### Opção A: Executar a Interface Web (FastAPI / Uvicorn)
Para iniciar a aplicação web interativa no seu navegador local:
```bash
docker run -p 8000:8000 --env-file .env --entrypoint "" csv-ai-agent uvicorn app:app --host 0.0.0.0 --port 8000
```
- Acesse **[http://localhost:8000](http://localhost:8000)** no seu navegador.
- Você poderá subir arquivos CSV via drag-and-drop, enviar perguntas, ver a execução passo a passo do fluxo e interagir no painel de validação humana.

#### Opção B: Executar a Interface de Linha de Comando (CLI)
Para rodar consultas diretamente pelo terminal:
```bash
docker run --env-file .env -v $(pwd)/data:/app/data -it csv-ai-agent --csv data/sample.csv --query "Qual é a média de idade de mulheres com churn?"
```
*(Nota: O parâmetro `-v $(pwd)/data:/app/data` faz o mapeamento do seu diretório local de dados para dentro do container, garantindo que o agente consiga ler os arquivos CSV).*

---

## 4. Desenvolvimento Local (Opcional - Sem Docker)

Caso prefira executar nativamente no seu ambiente de desenvolvimento local:

1. **Criar e ativar o ambiente virtual Python 3.11**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows use: .venv\Scripts\activate
   ```
2. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Executar a aplicação Web**:
   ```bash
   python -m uvicorn app:app --reload --port 8000
   ```
4. **Executar os testes unitários**:
   ```bash
   pytest
   ```
