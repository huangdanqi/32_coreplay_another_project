"""
Sub-Agent Management System for the diary agent.
Handles agent lifecycle management, initialization, configuration loading, and failure handling.
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from datetime import datetime, timedelta

from diary_agent.agents.base_agent import BaseSubAgent, AgentRegistry, AgentFactory
from diary_agent.core.llm_manager import LLMConfigManager, LLMProviderError
from diary_agent.utils.data_models import EventData, DiaryEntry, DataReader
from diary_agent.integration.weather_data_reader import WeatherDataReader
from diary_agent.integration.trending_data_reader import TrendingDataReader
from diary_agent.integration.holiday_data_reader import HolidayDataReader
from diary_agent.integration.friends_data_reader import FriendsDataReader
from diary_agent.integration.frequency_data_reader import FrequencyDataReader
from diary_agent.integration.adoption_data_reader import AdoptionDataReader
from diary_agent.integration.interaction_data_reader import InteractionDataReader
from diary_agent.integration.dialogue_data_reader import DialogueDataReader
from diary_agent.integration.neglect_data_reader import NeglectDataReader


class AgentFailureError(Exception):
    """Exception raised when agent operations fail."""
    pass


class SubAgentManager:
    """
    Manages the lifecycle of all sub-agents in the diary system.
    Handles initialization, configuration loading, failure handling, and retry logic.
    """
    
    def __init__(self, 
                 llm_manager: LLMConfigManager,
                 config_dir: str = "diary_agent/config",
                 max_retry_attempts: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the SubAgentManager.
        
        Args:
            llm_manager: LLM configuration manager
            config_dir: Directory containing agent configurations
            max_retry_attempts: Maximum retry attempts for failed operations
            retry_delay: Base delay between retries in seconds
        """
        self.llm_manager = llm_manager
        self.config_dir = Path(config_dir)
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay
        
        # Core components
        self.registry = AgentRegistry()
        self.factory = AgentFactory(llm_manager, str(self.config_dir / "agent_prompts"))
        
        # Agent management
        self.agents: Dict[str, BaseSubAgent] = {}
        self.data_readers: Dict[str, DataReader] = {}
        self.agent_health: Dict[str, Dict[str, Any]] = {}
        self.failure_counts: Dict[str, int] = {}
        
        # Configuration
        self.agent_config_path = self.config_dir / "agent_configuration.json"
        self.agent_configurations: Dict[str, Dict[str, Any]] = {}
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize system
        self._load_agent_configurations()
        self._initialize_data_readers()
    
    def _load_agent_configurations(self):
        """Load agent configuration from file."""
        try:
            if not self.agent_config_path.exists():
                self._create_default_agent_configuration()
            
            with open(self.agent_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.agent_configurations = config_data.get("agents", {})
            self.logger.info(f"Loaded configurations for {len(self.agent_configurations)} agent types")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Failed to load agent configuration: {str(e)}")
            self._create_default_agent_configuration()
    
    def _create_default_agent_configuration(self):
        """Create default agent configuration file."""
        default_config = {
            "agents": {
                "weather_agent": {
                    "class_name": "WeatherAgent",
                    "module_path": "diary_agent.agents.weather_agent",
                    "data_reader": "weather_data_reader",
                    "enabled": True,
                    "priority": 1
                },
                "trending_agent": {
                    "class_name": "TrendingAgent", 
                    "module_path": "diary_agent.agents.trending_agent",
                    "data_reader": "trending_data_reader",
                    "enabled": True,
                    "priority": 2
                },
                "holiday_agent": {
                    "class_name": "HolidayAgent",
                    "module_path": "diary_agent.agents.holiday_agent", 
                    "data_reader": "holiday_data_reader",
                    "enabled": True,
                    "priority": 3
                },
                "friends_agent": {
                    "class_name": "FriendsAgent",
                    "module_path": "diary_agent.agents.friends_agent",
                    "data_reader": "friends_data_reader", 
                    "enabled": True,
                    "priority": 4
                },
                "same_frequency_agent": {
                    "class_name": "SameFrequencyAgent",
                    "module_path": "diary_agent.agents.same_frequency_agent",
                    "data_reader": "frequency_data_reader",
                    "enabled": True,
                    "priority": 5
                },
                "adoption_agent": {
                    "class_name": "AdoptionAgent",
                    "module_path": "diary_agent.agents.adoption_agent",
                    "data_reader": "adoption_data_reader",
                    "enabled": True,
                    "priority": 6
                },
                "interactive_agent": {
                    "class_name": "InteractiveAgent",
                    "module_path": "diary_agent.agents.interactive_agent",
                    "data_reader": "interaction_data_reader",
                    "enabled": True,
                    "priority": 7
                },
                "dialogue_agent": {
                    "class_name": "DialogueAgent",
                    "module_path": "diary_agent.agents.dialogue_agent",
                    "data_reader": "dialogue_data_reader",
                    "enabled": True,
                    "priority": 8
                },
                "neglect_agent": {
                    "class_name": "NeglectAgent",
                    "module_path": "diary_agent.agents.neglect_agent",
                    "data_reader": "neglect_data_reader",
                    "enabled": True,
                    "priority": 9
                }
            }
        }
        
        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.agent_config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self.agent_configurations = default_config["agents"]
    
    def _initialize_data_readers(self):
        """Initialize data readers for all agent types."""
        data_reader_classes = {
            "weather_data_reader": WeatherDataReader,
            "trending_data_reader": TrendingDataReader,
            "holiday_data_reader": HolidayDataReader,
            "friends_data_reader": FriendsDataReader,
            "frequency_data_reader": FrequencyDataReader,
            "adoption_data_reader": AdoptionDataReader,
            "interaction_data_reader": InteractionDataReader,
            "dialogue_data_reader": DialogueDataReader,
            "neglect_data_reader": NeglectDataReader
        }
        
        for reader_name, reader_class in data_reader_classes.items():
            try:
                self.data_readers[reader_name] = reader_class()
                self.logger.info(f"Initialized data reader: {reader_name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize data reader {reader_name}: {str(e)}")
    
    async def initialize_agents(self) -> bool:
        """
        Initialize all configured agents.
        
        Returns:
            True if all agents initialized successfully, False otherwise
        """
        success_count = 0
        total_agents = len([config for config in self.agent_configurations.values() if config.get("enabled", True)])
        
        for agent_type, config in self.agent_configurations.items():
            if not config.get("enabled", True):
                self.logger.info(f"Skipping disabled agent: {agent_type}")
                continue
            
            try:
                success = await self._initialize_single_agent(agent_type, config)
                if success:
                    success_count += 1
                    self.logger.info(f"Successfully initialized agent: {agent_type}")
                else:
                    self.logger.error(f"Failed to initialize agent: {agent_type}")
                    
            except Exception as e:
                self.logger.error(f"Exception initializing agent {agent_type}: {str(e)}")
        
        self.logger.info(f"Initialized {success_count}/{total_agents} agents")
        return success_count == total_agents
    
    async def _initialize_single_agent(self, agent_type: str, config: Dict[str, Any]) -> bool:
        """
        Initialize a single agent.
        
        Args:
            agent_type: Type identifier for the agent
            config: Agent configuration dictionary
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Get data reader
            reader_name = config.get("data_reader")
            if not reader_name or reader_name not in self.data_readers:
                self.logger.error(f"Data reader not found for agent {agent_type}: {reader_name}")
                return False
            
            data_reader = self.data_readers[reader_name]
            
            # Import agent class dynamically
            module_path = config.get("module_path")
            class_name = config.get("class_name")
            
            if not module_path or not class_name:
                self.logger.error(f"Missing module_path or class_name for agent {agent_type}")
                return False
            
            # Dynamic import
            import importlib
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Create agent using factory
            agent = self.factory.create_agent(agent_type, agent_class, data_reader)
            
            if not agent:
                self.logger.error(f"Factory failed to create agent: {agent_type}")
                return False
            
            # Register agent
            self.agents[agent_type] = agent
            self.registry.register_agent(agent)
            
            # Initialize health tracking
            self.agent_health[agent_type] = {
                "status": "healthy",
                "last_success": datetime.now(),
                "last_failure": None,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0
            }
            
            self.failure_counts[agent_type] = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {agent_type}: {str(e)}")
            return False
    
    async def process_event_with_retry(self, event_data: EventData) -> Optional[DiaryEntry]:
        """
        Process event with automatic retry and failure handling.
        
        Args:
            event_data: Event data to process
            
        Returns:
            Generated diary entry or None if all attempts fail
        """
        # Find appropriate agent
        agent = self.registry.get_agent_for_event(event_data.event_name)
        if not agent:
            self.logger.warning(f"No agent found for event: {event_data.event_name}")
            return None
        
        agent_type = agent.get_agent_type()
        
        # Attempt processing with retry logic
        for attempt in range(self.max_retry_attempts):
            try:
                # Update health tracking
                self.agent_health[agent_type]["total_requests"] += 1
                
                # Process event
                diary_entry = await agent.process_event(event_data)
                
                # Update success metrics
                self.agent_health[agent_type]["successful_requests"] += 1
                self.agent_health[agent_type]["last_success"] = datetime.now()
                self.agent_health[agent_type]["status"] = "healthy"
                self.failure_counts[agent_type] = 0
                
                self.logger.info(f"Successfully processed event {event_data.event_name} with agent {agent_type}")
                return diary_entry
                
            except Exception as e:
                # Update failure metrics
                self.agent_health[agent_type]["failed_requests"] += 1
                self.agent_health[agent_type]["last_failure"] = datetime.now()
                self.failure_counts[agent_type] += 1
                
                self.logger.error(f"Attempt {attempt + 1} failed for agent {agent_type}: {str(e)}")
                
                # Check if we should retry
                if attempt < self.max_retry_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # Mark agent as unhealthy after max failures
                    if self.failure_counts[agent_type] >= self.max_retry_attempts:
                        self.agent_health[agent_type]["status"] = "unhealthy"
                    
                    self.logger.error(f"All retry attempts failed for agent {agent_type}")
        
        return None
    
    def get_agent(self, agent_type: str) -> Optional[BaseSubAgent]:
        """
        Get agent by type.
        
        Args:
            agent_type: Agent type identifier
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_type)
    
    def get_agent_for_event(self, event_name: str) -> Optional[BaseSubAgent]:
        """
        Get agent that handles a specific event.
        
        Args:
            event_name: Event name
            
        Returns:
            Agent instance or None if no agent handles this event
        """
        return self.registry.get_agent_for_event(event_name)
    
    def list_agents(self) -> List[str]:
        """Get list of all registered agent types."""
        return list(self.agents.keys())
    
    def list_supported_events(self) -> List[str]:
        """Get list of all supported event names."""
        return self.registry.list_supported_events()
    
    def get_agent_health(self, agent_type: str = None) -> Dict[str, Any]:
        """
        Get health status for agents.
        
        Args:
            agent_type: Specific agent type, or None for all agents
            
        Returns:
            Health status dictionary
        """
        if agent_type:
            return self.agent_health.get(agent_type, {})
        else:
            return self.agent_health.copy()
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.
        
        Returns:
            System status dictionary
        """
        total_agents = len(self.agents)
        healthy_agents = len([h for h in self.agent_health.values() if h.get("status") == "healthy"])
        
        total_requests = sum(h.get("total_requests", 0) for h in self.agent_health.values())
        successful_requests = sum(h.get("successful_requests", 0) for h in self.agent_health.values())
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": total_agents - healthy_agents,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": round(success_rate, 2),
            "supported_events": len(self.list_supported_events()),
            "llm_provider_status": self.llm_manager.get_provider_status()
        }
    
    async def restart_agent(self, agent_type: str) -> bool:
        """
        Restart a specific agent.
        
        Args:
            agent_type: Agent type to restart
            
        Returns:
            True if restart successful, False otherwise
        """
        if agent_type not in self.agent_configurations:
            self.logger.error(f"No configuration found for agent: {agent_type}")
            return False
        
        try:
            # Remove existing agent
            if agent_type in self.agents:
                del self.agents[agent_type]
            
            # Reinitialize
            config = self.agent_configurations[agent_type]
            success = await self._initialize_single_agent(agent_type, config)
            
            if success:
                self.logger.info(f"Successfully restarted agent: {agent_type}")
            else:
                self.logger.error(f"Failed to restart agent: {agent_type}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Exception restarting agent {agent_type}: {str(e)}")
            return False
    
    async def restart_unhealthy_agents(self) -> Dict[str, bool]:
        """
        Restart all unhealthy agents.
        
        Returns:
            Dictionary mapping agent types to restart success status
        """
        unhealthy_agents = [
            agent_type for agent_type, health in self.agent_health.items()
            if health.get("status") == "unhealthy"
        ]
        
        results = {}
        for agent_type in unhealthy_agents:
            self.logger.info(f"Restarting unhealthy agent: {agent_type}")
            results[agent_type] = await self.restart_agent(agent_type)
        
        return results
    
    def reload_configurations(self):
        """Reload all configurations from files."""
        try:
            # Reload agent configurations
            self._load_agent_configurations()
            
            # Reload LLM configurations
            self.llm_manager.reload_configuration()
            
            # Reload prompt configurations
            self.factory.reload_prompt_configurations()
            
            self.logger.info("All configurations reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to reload configurations: {str(e)}")
    
    async def shutdown(self):
        """Gracefully shutdown all agents and cleanup resources."""
        self.logger.info("Shutting down SubAgentManager...")
        
        # Clear agents
        self.agents.clear()
        
        # Clear health tracking
        self.agent_health.clear()
        self.failure_counts.clear()
        
        self.logger.info("SubAgentManager shutdown complete")