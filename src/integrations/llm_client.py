# FILE: src/integrations/llm_client.py
from __future__ import annotations

import json
from typing import Any, Optional

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class LLMClient:
    """
    Thin wrapper that always returns parsed JSON.

    Important:
    Some Azure deployments only support the default temperature (1).
    So we do NOT set temperature at all.
    """

    def __init__(
        self,
        azure_endpoint: str | None,
        api_key: str | None,
        api_version: str | None,
        deployment_name: str | None,
    ):
        self.enabled = bool(
            azure_endpoint and api_key and api_version and deployment_name)

        self._llm: Optional[AzureChatOpenAI] = None
        if self.enabled:
            self._llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version,
                deployment_name=deployment_name,
                # Do not set temperature here.
            )

    def invoke_json(self, system_rules: str, user_prompt: str, max_retries: int = 2) -> dict[str, Any]:
        if not self.enabled or not self._llm:
            raise RuntimeError(
                "LLM is not configured. Check .env / AppConfig.")

        messages = [
            SystemMessage(content=system_rules),
            HumanMessage(content=user_prompt),
        ]

        last_err: Exception | None = None
        for _ in range(max_retries + 1):
            try:
                res = self._llm.invoke(messages)
                text = (res.content or "").strip()
                return json.loads(text)
            except Exception as e:
                last_err = e

        raise RuntimeError(f"LLM JSON invoke failed: {last_err}")
