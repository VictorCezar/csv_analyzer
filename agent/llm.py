import os
from langchain_ollama import ChatOllama, OllamaEmbeddings

def get_llm(temperature: float = 0.0) -> ChatOllama:
    """
    Initialize and return the local ChatOllama LLM.
    
    Args:
        temperature: The temperature parameter for the LLM.
        
    Returns:
        ChatOllama: The configured LangChain ChatOllama instance.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    
    return ChatOllama(
        base_url=base_url,
        model=model,
        temperature=temperature,
    )

def get_embeddings() -> OllamaEmbeddings:
    """
    Initialize and return local OllamaEmbeddings.
    
    Returns:
        OllamaEmbeddings: The configured LangChain OllamaEmbeddings instance.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    
    return OllamaEmbeddings(
        base_url=base_url,
        model=model,
    )
