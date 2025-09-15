#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from diary_agent.core.llm_manager import LLMConfigManager


class EventExtractionAgent:
    def __init__(self, prompt_path: str = None, llm_config_path: str = "config/llm_configuration.json") -> None:
        self.llm_manager = LLMConfigManager(config_path=llm_config_path)
        if prompt_path is None:
            prompt_path = Path(__file__).parent / "prompt.json"
        self.prompt = json.loads(Path(prompt_path).read_text(encoding="utf-8"))

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = self.prompt.get("system_prompt", "")
        tmpl = self.prompt.get("user_prompt_template", "{dialogue}")
        user_prompt = tmpl.format(dialogue=payload.get("dialogue", ""))

        text = await self.llm_manager.generate_text_with_failover(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        try:
            data = json.loads(text)
        except Exception:
            data = {"summary": text.strip()[:50]}

        return {
            "chat_uuid": payload.get("chat_uuid", ""),
            "chat_event_uuid": payload.get("chat_event_uuid", ""),
            "memory_uuid": payload.get("memory_uuid", ""),
            "topic": data.get("topic", ""),
            "title": data.get("title", ""),
            "summary": (data.get("summary", "") or "")[:50],
            "type": "new",
            "emotion": data.get("emotion", []),
            "created_at": datetime.now().isoformat()
        }


