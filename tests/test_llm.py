import os
from unittest.mock import patch
from agent.llm import get_llm, get_embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings

def test_get_llm_config():
    """Test that get_llm instantiates ChatOllama with configured environment variables."""
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://test-server:11434", "OLLAMA_MODEL": "test-model"}):
        llm = get_llm(temperature=0.5)
        assert isinstance(llm, ChatOllama)
        assert llm.base_url == "http://test-server:11434"
        assert llm.model == "test-model"
        assert llm.temperature == 0.5

def test_get_embeddings_config():
    """Test that get_embeddings instantiates OllamaEmbeddings with configured environment variables."""
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://test-server:11434", "OLLAMA_EMBEDDING_MODEL": "test-embed"}):
        embeddings = get_embeddings()
        assert isinstance(embeddings, OllamaEmbeddings)
        assert embeddings.base_url == "http://test-server:11434"
        assert embeddings.model == "test-embed"
