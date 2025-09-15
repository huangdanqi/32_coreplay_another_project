#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event pipeline that links EventExtractionAgent -> EventUpdateAgent

Usage (programmatic):
  result = await run_pipeline(dialogue_payload, related_events)
"""

from typing import Dict, Any, List

from .event_extraction_agent.agent import EventExtractionAgent
from .event_update_agent.agent import EventUpdateAgent


class EventPipeline:
    def __init__(self) -> None:
        self.extractor = EventExtractionAgent()
        self.updater = EventUpdateAgent()

    async def run(self, dialogue_payload: Dict[str, Any], related_events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        extraction = await self.extractor.run(dialogue_payload)
        update = await self.updater.run(extraction, related_events or [])
        return {
            "extraction": extraction,
            "update": update
        }


