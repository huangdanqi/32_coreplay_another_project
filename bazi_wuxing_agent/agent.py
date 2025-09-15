#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

from diary_agent.core.llm_manager import LLMConfigManager


class BaziWuxingAgent:
    """Agent to calculate BaZi (八字) and WuXing (五行) from birth info.

    Input payload expects keys:
      - birth_year, birth_month, birth_day, birth_hour (ints or strings)
      - birthplace (string)
    Output:
      - bazi: list[str] 8 characters
      - wuxing: list[str] up to 6 elements
    """

    def __init__(self, prompt_path: str = None, llm_config_path: str = "config/llm_configuration.json") -> None:
        self.llm_manager = LLMConfigManager(config_path=llm_config_path)
        if prompt_path is None:
            prompt_path = Path(__file__).parent / "prompt.json"
        self.prompt = json.loads(Path(prompt_path).read_text(encoding="utf-8"))

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Optional: allow caller to choose provider and force LLM usage
        provider = (payload or {}).get("provider")
        if provider:
            try:
                self.llm_manager.set_default_provider(str(provider))
            except Exception:
                pass
        system_prompt = self.prompt.get("system_prompt", "")
        tmpl = self.prompt.get("user_prompt_template", "{birth_json}")
        user_prompt = tmpl.format(birth_json=json.dumps(payload, ensure_ascii=False))

        print(f"🔮 BaZi Agent - Input payload: {payload}")
        print(f"🔮 BaZi Agent - User prompt: {user_prompt}")

        text = await self.llm_manager.generate_text_with_failover(
            prompt=user_prompt,
            system_prompt=system_prompt
        )

        print(f"🔮 BaZi Agent - LLM response: {text}")

        try:
            data = json.loads(text)
            print(f"🔮 BaZi Agent - Parsed JSON: {data}")
        except Exception as e:
            print(f"🔮 BaZi Agent - JSON parse failed: {e}")
            data = {"bazi": [], "wuxing": []}

        bazi = data.get("bazi") or []
        wuxing = data.get("wuxing") or []
        if isinstance(bazi, str):
            bazi = list(bazi)[:8]
        if isinstance(wuxing, str):
            wuxing = [w.strip() for w in wuxing.split() if w.strip()][:6]

        print(f"🔮 BaZi Agent - Extracted bazi: {bazi}, wuxing: {wuxing}")

        # Offline deterministic fallback if LLM returned nothing (unless force_llm)
        force_llm = bool((payload or {}).get("force_llm"))
        if (not bazi or not wuxing) and not force_llm:
            print(f"🔮 BaZi Agent - Using fallback calculation")
            fb_bazi, fb_wuxing = self._fallback_calc(payload)
            print(f"🔮 BaZi Agent - Fallback result: bazi={fb_bazi}, wuxing={fb_wuxing}")
            if not bazi:
                bazi = fb_bazi
            if not wuxing:
                wuxing = fb_wuxing

        result = {"bazi": bazi[:8], "wuxing": wuxing[:6]}
        print(f"🔮 BaZi Agent - Final result: {result}")
        return result

    # -------------------- Deterministic Fallback --------------------
    def _fallback_calc(self, payload: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        stems = list("甲乙丙丁戊己庚辛壬癸")
        branches = list("子丑寅卯辰巳午未申酉戌亥")
        # Map GanZhi to WuXing
        wuxing_map = {
            "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
            "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
            "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
            "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
            "戌": "土", "亥": "水"
        }

        try:
            year = int(payload.get("birth_year"))
            month = int(payload.get("birth_month"))
            day = int(payload.get("birth_day"))
            hour = int(payload.get("birth_hour"))
        except Exception:
            # Fallback inputs if missing
            year, month, day, hour = 2000, 1, 1, 0

        # Year pillar (accurate)
        y_stem_idx = (year - 4) % 10
        y_branch_idx = (year - 4) % 12
        y_stem, y_branch = stems[y_stem_idx], branches[y_branch_idx]

        # Month pillar (approximation; uses solar-like mapping)
        month_branches_cycle = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
        m_branch = month_branches_cycle[(month - 1) % 12]
        # Month stem: simple derivation from year stem
        m_stem_idx = (y_stem_idx * 2 + month) % 10
        m_stem = stems[m_stem_idx]

        # Day pillar (rough; based on ordinal days since 1900-01-01)
        try:
            base = datetime(1900, 1, 1)
            curr = datetime(year, month, day)
            days = (curr - base).days
        except Exception:
            days = 0
        d_idx = days % 60
        d_stem, d_branch = stems[d_idx % 10], branches[d_idx % 12]

        # Hour pillar
        hour_branches = [
            (23, "子"), (1, "丑"), (3, "寅"), (5, "卯"), (7, "辰"), (9, "巳"),
            (11, "午"), (13, "未"), (15, "申"), (17, "酉"), (19, "戌"), (21, "亥")
        ]
        # Derive branch by hour window (two-hour blocks starting at 23)
        h_branch = "子"
        for start_hour, br in hour_branches:
            if hour >= start_hour or (start_hour == 23 and hour < 1):
                h_branch = br
        # Hour stem derived from day stem
        h_branch_idx = branches.index(h_branch)
        h_stem_idx = (d_stem and stems.index(d_stem)) if isinstance(d_stem, str) else (d_idx % 10)
        h_stem_idx = (h_stem_idx * 2 + h_branch_idx) % 10
        h_stem = stems[h_stem_idx]

        bazi = [y_stem, y_branch, m_stem, m_branch, d_stem, d_branch, h_stem, h_branch]

        # Aggregate WuXing counts
        counts: Dict[str, int] = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        for ch in bazi:
            element = wuxing_map.get(ch)
            if element:
                counts[element] += 1
        # Sort by count desc, then a fixed order
        order = ["金", "木", "水", "火", "土"]
        sorted_elements = sorted(order, key=lambda e: (-counts[e], order.index(e)))
        wuxing = [e for e in sorted_elements if counts[e] > 0][:6]
        if not wuxing:
            wuxing = ["金", "木", "水", "火", "土"]

        return bazi, wuxing


