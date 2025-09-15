#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import asyncio
from typing import Dict, Any, List

from event_agents.extraction.agent import EventExtractionAgent
from event_agents.update.agent import EventUpdateAgent


class EventPipeline:
    def __init__(self) -> None:
        self.extractor = EventExtractionAgent()
        self.updater = EventUpdateAgent()

    async def run(self, dialogue_payload: Dict[str, Any], related_events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        extraction = await self.extractor.run(dialogue_payload)
        update = await self.updater.run(extraction, related_events or [])
        return {"extraction": extraction, "update": update}


async def main():
    import sys
    payload = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {
        "chat_uuid": "sample_chat",
        "chat_event_uuid": "sample_event",
        "memory_uuid": "sample_memory",
        "dialogue": "你好，今天考试压力大，但朋友安慰了我。"
    }
    pipeline = EventPipeline()
    result = await pipeline.run(payload, related_events=[])
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())


