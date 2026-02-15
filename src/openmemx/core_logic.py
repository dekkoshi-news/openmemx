import math
import json
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
import ssl
import os
import certifi

# Fix SSL certificate issues (especially on macOS)
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Universal SSL bypass for environment issues (macOS Python) fallback
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

class MemoryLogic:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Local model for embeddings and basic surprise proxy
        self.model = SentenceTransformer(model_name)
        
    def calculate_surprise(self, new_content: str, historical_contents: List[str]) -> float:
        """
        Calculates a proxy for Bayesian Surprise using semantic distance.
        High distance from existing memories implies high surprise.
        """
        if not historical_contents:
            return 1.0  # Initial content is always surprising
            
        new_embedding = self.model.encode([new_content])[0]
        hist_embeddings = self.model.encode(historical_contents)
        
        # Calculate cosine similarity with all historical contents
        similarities = np.dot(hist_embeddings, new_embedding) / (
            np.linalg.norm(hist_embeddings, axis=1) * np.linalg.norm(new_embedding)
        )
        
        # Surprise is 1 - max_similarity (higher distance = higher surprise)
        max_sim = np.max(similarities)
        surprise = 1.0 - max_sim
        
        return float(surprise)


class PromptCompressor:
    def __init__(self):
        # LLMLingua-2 proxy or integration
        # Note: llmlingua requires a model to be loaded.
        from llmlingua import PromptCompressor as LLMCompressor
        self.compressor = None # Delay initialization to avoid startup lag

    def compress(self, context: str, instruction: str = "", target_token: int = 500) -> str:
        if self.compressor is None:
            from llmlingua import PromptCompressor as LLMCompressor
            self.compressor = LLMCompressor()
            
        result = self.compressor.compress_prompt(
            context,
            instruction=instruction,
            target_token=target_token,
            condition_compare=True,
            condition_in_question=True,
            rank_method="longllmlingua",
            use_llmlingua2=True
        )
        return result['compressed_prompt']
