#!/usr/bin/env python3
"""
Event Lookup Utility
Provides quick access to event information for development and testing.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.event_manager import EventManager

def main():
    """Main function for event lookup utility."""
    
    if len(sys.argv) < 2:
        print("Event Lookup Utility")
        print("=" * 50)
        print("Usage:")
        print("  python event_lookup.py <command> [args]")
        print("\nCommands:")
        print("  list                    - List all events")
        print("  agents                  - List all agent types")
        print("  event <name>           - Get event details")
        print("  agent <type>           - Get events for agent")
        print("  category <name>        - Get category details")
        print("  weather                - Get weather events")
        print("  weights <role>         - Get role weights")
        print("  tags <type>            - Get emotional tags")
        print("  summary                - Show full summary")
        return
    
    try:
        manager = EventManager()
        command = sys.argv[1].lower()
        
        if command == "list":
            events = manager.list_all_events()
            print(f"📋 All Events ({len(events)}):")
            for i, event in enumerate(events, 1):
                print(f"  {i:2d}. {event}")
        
        elif command == "agents":
            agents = manager.list_all_agents()
            print(f"🤖 All Agent Types ({len(agents)}):")
            for i, agent in enumerate(agents, 1):
                event_count = len(manager.get_events_by_agent(agent))
                print(f"  {i:2d}. {agent} ({event_count} events)")
        
        elif command == "event" and len(sys.argv) > 2:
            event_name = sys.argv[2]
            event = manager.get_event(event_name)
            if event:
                print(f"🎯 Event: {event.name}")
                print(f"   Description: {event.description}")
                print(f"   Category: {event.category}")
                print(f"   Agent: {event.agent_type}")
                print(f"   Emotional Impact: {event.emotional_impact}")
                print(f"   Weight Key: {event.weight_key}")
                print(f"   Requires Weather API: {event.requires_weather_api}")
                print(f"   Requires User Preferences: {event.requires_user_preferences}")
            else:
                print(f"❌ Event '{event_name}' not found")
        
        elif command == "agent" and len(sys.argv) > 2:
            agent_type = sys.argv[2]
            events = manager.get_events_by_agent(agent_type)
            if events:
                print(f"🤖 Agent: {agent_type} ({len(events)} events)")
                for event in events:
                    impact_icon = "✅" if event.emotional_impact == "positive" else "❌" if event.emotional_impact == "negative" else "⚪"
                    print(f"   {impact_icon} {event.name}: {event.description}")
            else:
                print(f"❌ Agent '{agent_type}' not found")
        
        elif command == "category" and len(sys.argv) > 2:
            category_name = sys.argv[2]
            category = manager.get_category(category_name)
            if category:
                print(f"🏷️  Category: {category.name}")
                print(f"   Description: {category.description}")
                print(f"   Agent: {category.agent_type}")
                print(f"   Events ({len(category.events)}):")
                for event_name, event in category.events.items():
                    impact_icon = "✅" if event.emotional_impact == "positive" else "❌" if event.emotional_impact == "negative" else "⚪"
                    print(f"     {impact_icon} {event_name}: {event.description}")
            else:
                print(f"❌ Category '{category_name}' not found")
        
        elif command == "weather":
            events = manager.get_weather_events()
            print(f"🌤️  Weather Events ({len(events)}):")
            for event in events:
                impact_icon = "✅" if event.emotional_impact == "positive" else "❌" if event.emotional_impact == "negative" else "⚪"
                weight_info = f" (weight: {event.weight_key})" if event.weight_key else ""
                print(f"   {impact_icon} {event.name}: {event.description}{weight_info}")
        
        elif command == "weights" and len(sys.argv) > 2:
            role = sys.argv[2]
            weights = manager.get_role_weights(role)
            if weights:
                print(f"⚖️  Role Weights for '{role}':")
                for event_type, weight in weights.items():
                    print(f"   {event_type}: {weight}")
            else:
                print(f"❌ Role '{role}' not found")
        
        elif command == "tags" and len(sys.argv) > 2:
            tag_type = sys.argv[2]
            tags = manager.get_emotional_tags(tag_type)
            if tags:
                print(f"😊 Emotional Tags for '{tag_type}':")
                for i, tag in enumerate(tags, 1):
                    print(f"   {i}. {tag}")
            else:
                print(f"❌ Tag type '{tag_type}' not found")
        
        elif command == "summary":
            manager.print_summary()
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python event_lookup.py' for help")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()