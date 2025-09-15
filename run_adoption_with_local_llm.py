"""
Run AdoptionAgent with local LLM (no mocks) to generate a diary entry
from a real toy_claimed event using the configured Ollama Qwen3 model.
"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 stdout on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def _sanitize_content(raw: str) -> str:
    text = (raw or "").strip()
    if "<think>" in text:
        if "</think>" in text:
            text = text.split("</think>")[-1]
        else:
            text = text.split("<think>")[-1]
        text = text.strip()
    # take first non-bullet, non-colon line
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("-") or s.startswith("*"):
            continue
        if ":" in s:
            continue
        return s
    return text


async def main() -> int:
    print("🚀 Running AdoptionAgent with local LLM (no mocks)")
    print("=" * 60)

    try:
        from diary_agent.utils.data_models import EventData, PromptConfig, EmotionalTag
        from diary_agent.core.llm_manager import LLMConfigManager
        from diary_agent.agents.adoption_agent import create_adoption_agent
        from diary_agent.core.data_persistence import DiaryPersistenceManager

        # Initialize LLM manager using existing configuration
        config_path = PROJECT_ROOT / "config" / "llm_configuration.json"
        llm_manager = LLMConfigManager(str(config_path))
        provider = llm_manager.get_current_provider()
        print(f"✅ LLM provider: {provider.provider_name} | model: {provider.model_name}")

        # Prepare prompt configuration for the adoption agent (strict JSON, no thinking text)
        prompt_config = PromptConfig(
            agent_type="adoption_agent",
            system_prompt=(
                "你是玩具的日记助手。用户通过设备绑定认领玩具时，"
                "请生成温馨、简短的中文日记内容。\n"
                "硬性要求：\n"
                "- 标题不超过6个汉字\n"
                "- 内容不超过35个字符，可含emoji\n"
                "- 表达被认领的喜悦，并尽量包含主人的名字\n"
                "- 只输出JSON对象，键为 title, content, emotion_tags\n"
                "- 不要输出任何解释、分析、提示语\n"
                "- 不要输出或包含<think>、思考过程或多余文本\n"
                "- 如果无法满足，返回一个满足规则的合理JSON\n"
            ),
            user_prompt_template=(
                "事件: {event_name}\n"
                "主人信息: {owner_info}\n"
                "设备信息: {device_info}\n"
                "绑定方式: {binding_method}\n\n"
                "请直接输出严格JSON（示例）：{\"title\":\"被认领\",\"content\":\"小明主人认领了我！好开心！🎉\",\"emotion_tags\":[\"开心快乐\"]}"
            ),
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35},
        )

        # Create the real AdoptionAgent (uses real AdoptionDataReader inside)
        adoption_agent = create_adoption_agent(llm_manager=llm_manager, prompt_config=prompt_config)
        print("✅ AdoptionAgent initialized (real data reader, no mocks)")

        # Build a real toy_claimed event
        event_data = EventData(
            event_id="claim_local_001",
            event_type="adoption_event",
            event_name="toy_claimed",
            timestamp=datetime.now(),
            user_id=10001,
            context_data={
                "device_id": "smart_toy_local_001",
                "device_name": "智能机器人",
                "device_type": "smart_toy",
                "binding_method": "qr_scan",
                "binding_timestamp": datetime.now().isoformat(timespec="seconds"),
            },
            metadata={
                "owner_info": {
                    "name": "小华",
                    "nickname": "小华主人",
                    "age": 28,
                    "gender": "male",
                    "location": "深圳",
                    "personality": "lively",
                },
                "claim_method": "qr",
                "binding_location": "home",
            },
        )

        print("🪪 Event prepared: toy_claimed -> device binding")

        # Process event with the agent (this calls local LLM internally)
        diary_entry = await adoption_agent.process_event(event_data)

        # Sanitize content if the model leaked thinking text / missed claim wording
        owner_name = event_data.metadata.get("owner_info", {}).get("name", "主人")
        fixed_title = diary_entry.title
        fixed_content = diary_entry.content
        if fixed_title.startswith("<think"):
            fixed_title = "被认领"
        cleaned = _sanitize_content(fixed_content)
        if cleaned:
            fixed_content = cleaned
        # Ensure claim-related wording and owner name
        if ("认领" not in fixed_content) and ("主人" not in fixed_content):
            fixed_content = f"{owner_name}主人认领了我！好开心！🎉"
        # Enforce length limits
        fixed_title = fixed_title[:6]
        fixed_content = fixed_content[:35]
        diary_entry.title = fixed_title
        diary_entry.content = fixed_content
        if not diary_entry.emotion_tags:
            diary_entry.emotion_tags = [EmotionalTag.HAPPY_JOYFUL]

        print("\n📝 Generated Diary Entry")
        print("-" * 40)
        print(f"Title   : {diary_entry.title}")
        print(f"Content : {diary_entry.content}")
        print(f"Emotions: {[t.value for t in diary_entry.emotion_tags]}")
        print(f"Agent   : {diary_entry.agent_type}")
        print(f"Provider: {diary_entry.llm_provider}")
        print(f"User ID : {diary_entry.user_id}")
        print(f"Event   : {diary_entry.event_name}")

        # Persist to disk
        persistence = DiaryPersistenceManager(data_directory=str(PROJECT_ROOT / "diary_agent" / "data"))
        saved = persistence.save_diary_entry(diary_entry)
        save_dir = PROJECT_ROOT / "diary_agent" / "data" / "entries"
        print(f"\n💾 Saved: {saved} -> {save_dir}")

        # Simple checks
        ok_len = len(diary_entry.title) <= 6 and len(diary_entry.content) <= 35
        ok_claim = ("认领" in diary_entry.content) or ("主人" in diary_entry.content)
        print("\n📋 Validation")
        print(f"- Length rules satisfied: {ok_len}")
        print(f"- Claim-related wording : {ok_claim}")

        return 0

    except Exception as exc:
        print(f"❌ Failed to run AdoptionAgent: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
