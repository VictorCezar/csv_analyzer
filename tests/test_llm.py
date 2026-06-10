import os
from unittest.mock import patch
from agent.llm import get_llm, get_embeddings
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

def test_get_llm_config():
    """Testa se o get_llm instancia o ChatGroq corretamente com a API Key."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "fake-key-for-test"}):
        llm = get_llm(temperature=0.5)
        assert isinstance(llm, ChatGroq)
        assert llm.model_name == "llama-3.1-8b-instant"
        assert llm.temperature == 0.5

def test_get_embeddings_config():
    """Testa se o get_embeddings instancia o HuggingFaceEmbeddings."""
    embeddings = get_embeddings()
    assert isinstance(embeddings, HuggingFaceEmbeddings)
    assert embeddings.model_name == "all-MiniLM-L6-v2"