#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from diary_agent.core.llm_manager import LLMConfigManager


class EventUpdateAgent:
    def __init__(self, prompt_path: str = None, llm_config_path: str = "config/llm_configuration.json") -> None:
        self.llm_manager = LLMConfigManager(config_path=llm_config_path)
        if prompt_path is None:
            prompt_path = Path(__file__).parent / "prompt.json"
        self.prompt = json.loads(Path(prompt_path).read_text(encoding="utf-8"))

    def _heuristic_merge(self, extraction: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Lightweight rule-based merge to ensure demo updates are produced."""
        if not history:
            return {"merged": False}
        topic = (extraction.get("topic") or "").strip()
        memory_uuid = extraction.get("memory_uuid")
        # Choose the first candidate that matches memory or topic
        candidate = None
        for h in history:
            if memory_uuid and h.get("memory_uuid") == memory_uuid:
                candidate = h
                break
            if topic and topic == (h.get("topic") or "").strip():
                candidate = h
                break
        if not candidate:
            # fallback: merge with the latest by created_at
            candidate = history[0]

        # Build updated_event
        updated_event = dict(candidate)
        # Title preference: keep existing, else use extraction
        if not (updated_event.get("title") or "").strip():
            updated_event["title"] = extraction.get("title", "")
        # Summary concatenation (truncate to reasonable length)
        new_summary = (candidate.get("summary", "") or "").strip()
        add_summary = (extraction.get("summary", "") or "").strip()
        if add_summary and add_summary not in new_summary:
            combined = (new_summary + (" | " if new_summary else "") + add_summary)
            updated_event["summary"] = combined[:200]
        # Emotions union
        emos = list(dict.fromkeys((candidate.get("emotion") or []) + (extraction.get("emotion") or [])))
        updated_event["emotion"] = emos
        updated_event["type"] = "update"
        updated_event["updated_at"] = datetime.now().isoformat()
        return {"merged": True, "merge_reason": "heuristic_merge", "updated_event": updated_event}

    async def run(self, extraction_result: Dict[str, Any], rag_memories: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        rag_memories = rag_memories or []

        # First try deterministic heuristic merge so demo reliably shows updates
        heuristic = self._heuristic_merge(extraction_result, rag_memories)
        if heuristic.get("merged"):
            return {
                "merged": True,
                "merge_reason": heuristic.get("merge_reason", "heuristic_merge"),
                "new_event": None,
                "updated_event": heuristic.get("updated_event"),
                "update_info": {"updated_by": "event_update_agent", "updated_at": datetime.now().isoformat()}
            }

        # Otherwise, fall back to LLM-based decision
        system_prompt = self.prompt.get("system_prompt", "")
        tmpl = self.prompt.get("user_prompt_template", "")
        user_prompt = tmpl.format(
            extraction_json=json.dumps(extraction_result, ensure_ascii=False),
            rag_json=json.dumps(rag_memories, ensure_ascii=False)
        )

        text = await self.llm_manager.generate_text_with_failover(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        try:
            data = json.loads(text)
        except Exception:
            data = {"merged": False, "merge_reason": text.strip()[:100]}

        return {
            "merged": bool(data.get("merged", False)),
            "merge_reason": data.get("merge_reason", ""),
            "new_event": data.get("new_event"),
            "updated_event": data.get("updated_event"),
            "update_info": {"updated_by": "event_update_agent", "updated_at": datetime.now().isoformat()}
        }


