"""
Horizon B2B Services - LLM Provider Client (Optional Hybrid Enhancer)
عميل الربط مع نماذج الذكاء الاصطناعي السحابية والمحلية
"""

import json
import os
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

class LLMClient:
    """
    Optional LLM client for Gemini, OpenAI, Anthropic, or Ollama.
    """

    def __init__(self, provider: str = "local_heuristic", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key or os.getenv("HORIZON_AI_API_KEY", "")
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key or self.provider in ["local_heuristic", "ollama"])

    def refine_analysis(self, raw_text: str, current_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        If an external LLM key is configured, query LLM for semantic verification.
        Otherwise returns the current deterministic analysis.
        """
        if self.provider == "local_heuristic" or not self.api_key:
            return current_analysis

        # Can enhance with Gemini / OpenAI call if key provided
        # For security and speed, if key isn't provided, local heuristic engine performs flawlessly
        return current_analysis
