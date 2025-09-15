#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

from event_agents.pipeline import EventPipeline


def pretty_print(title: str, data: Dict[str, Any]) -> None:
    print("\n" + title)
    print("-" * 60)
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def run_case(dialogue: str, related_events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {
        "chat_uuid": "chat-" + datetime.now().strftime("%H%M%S"),
        "chat_event_uuid": "evt-" + datetime.now().strftime("%f"),
        "memory_uuid": "mem-001",
        "dialogue": dialogue
    }
    pipeline = EventPipeline()
    return await pipeline.run(payload, related_events or [])


async def main() -> int:
    print("\n🚀 Event Agents Quick Test")
    print("=" * 60)

    # Case 1: No related events (expect merged=false)
    case1_dialogue = "今天考试压力有点大，但朋友安慰了我，心里好受些了。"
    res1 = await run_case(case1_dialogue, related_events=[])
    pretty_print("Case 1 - No related events", res1)

    # Case 2: Provide a related event with same topic to encourage merge
    # Note: topic will be inferred by the model in extraction; we supply a likely related past record
    related = [
        {
            "chat_uuid": "chat-history-1",
            "chat_event_uuid": "evt-history-1",
            "memory_uuid": "mem-001",
            "topic": "日常交流",
            "title": "考试担忧",
            "summary": "之前也为考试紧张，并得到朋友安慰。",
            "type": "new",
            "emotion": ["担忧", "平静"],
            "created_at": "2025-09-01T12:00:00"
        }
    ]
    case2_dialogue = "又要考试了，有点紧张，还好朋友继续鼓励我。"
    res2 = await run_case(case2_dialogue, related_events=related)
    pretty_print("Case 2 - With related event (expect possible merge)", res2)

    print("\n✅ Finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))


