import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def get_llm(temperature: float = 0.0) -> ChatGroq:
    """
    Inicializa e retorna o LLM Llama 3 rodando na nuvem ultrarrápida do Groq.
    
    Args:
        temperature: O parâmetro de criatividade/aleatoriedade.
        
    Returns:
        ChatGroq: Instância configurada do LangChain para o Groq.
    """
    # A biblioteca ChatGroq automaticamente busca a variável GROQ_API_KEY do ambiente.
    return ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=temperature,
    )

def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Inicializa e retorna os embeddings locais do HuggingFace.
    
    Returns:
        HuggingFaceEmbeddings: Instância configurada para vetorização local.
    """
    # O modelo all-MiniLM-L6-v2 é padrão da indústria: extremamente leve, 
    # roda rápido na CPU e não requer chave de API.
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )