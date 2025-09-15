"""
Comprehensive logging system for the diary agent.
Provides structured logging, log rotation, and monitoring capabilities.
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class DiaryAgentFormatter(logging.Formatter):
    """Custom formatter for diary agent logs with structured output."""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'component'):
            log_entry['component'] = record.component
        if hasattr(record, 'category'):
            log_entry['category'] = record.category
        if hasattr(record, 'retry_count'):
            log_entry['retry_count'] = record.retry_count
        if hasattr(record, 'metadata'):
            log_entry['metadata'] = record.metadata
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        if hasattr(record, 'agent_type'):
            log_entry['agent_type'] = record.agent_type
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class DiaryAgentLogger:
    """Central logging manager for the diary agent system."""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_level = getattr(logging, log_level.upper())
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup the root logger configuration."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str, component: str = None) -> logging.Logger:
        """Get or create a logger for a specific component."""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # File handler with rotation
        log_file = self.log_dir / f"{name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(DiaryAgentFormatter())
        
        logger.addHandler(file_handler)
        
        # Add component info if provided
        if component:
            logger = logging.LoggerAdapter(logger, {'component': component})
        
        self.loggers[name] = logger
        return logger
    
    def get_error_logger(self) -> logging.Logger:
        """Get dedicated error logger."""
        return self.get_logger("diary_agent.errors", "error_handler")
    
    def get_performance_logger(self) -> logging.Logger:
        """Get dedicated performance logger."""
        return self.get_logger("diary_agent.performance", "performance")
    
    def get_audit_logger(self) -> logging.Logger:
        """Get dedicated audit logger for tracking system events."""
        return self.get_logger("diary_agent.audit", "audit")
    
    def log_component_start(self, component_name: str, metadata: Dict[str, Any] = None):
        """Log component startup."""
        logger = self.get_logger(f"diary_agent.{component_name}", component_name)
        logger.info(
            f"Component {component_name} starting",
            extra={"metadata": metadata or {}}
        )
    
    def log_component_stop(self, component_name: str, metadata: Dict[str, Any] = None):
        """Log component shutdown."""
        logger = self.get_logger(f"diary_agent.{component_name}", component_name)
        logger.info(
            f"Component {component_name} stopping",
            extra={"metadata": metadata or {}}
        )
    
    def log_event_processing(self, event_type: str, agent_type: str, user_id: int, 
                           status: str, metadata: Dict[str, Any] = None):
        """Log event processing activities."""
        logger = self.get_audit_logger()
        logger.info(
            f"Event processing: {status}",
            extra={
                "event_type": event_type,
                "agent_type": agent_type,
                "user_id": user_id,
                "metadata": metadata or {}
            }
        )
    
    def log_llm_api_call(self, provider: str, model: str, tokens_used: int, 
                        response_time: float, status: str):
        """Log LLM API calls for monitoring."""
        logger = self.get_performance_logger()
        logger.info(
            f"LLM API call: {status}",
            extra={
                "provider": provider,
                "model": model,
                "tokens_used": tokens_used,
                "response_time": response_time,
                "metadata": {
                    "api_call": True,
                    "provider": provider,
                    "model": model
                }
            }
        )
    
    def log_diary_generation(self, user_id: int, event_type: str, agent_type: str,
                           title: str, content_length: int, emotion_tags: list):
        """Log diary entry generation."""
        logger = self.get_audit_logger()
        logger.info(
            "Diary entry generated",
            extra={
                "user_id": user_id,
                "event_type": event_type,
                "agent_type": agent_type,
                "metadata": {
                    "title_length": len(title),
                    "content_length": content_length,
                    "emotion_tags": emotion_tags
                }
            }
        )
    
    def log_error_recovery(self, component: str, error_category: str, 
                          recovery_action: str, success: bool):
        """Log error recovery attempts."""
        logger = self.get_error_logger()
        level = logging.INFO if success else logging.WARNING
        logger.log(
            level,
            f"Error recovery: {recovery_action}",
            extra={
                "component": component,
                "category": error_category,
                "recovery_action": recovery_action,
                "success": success
            }
        )
    
    def log_circuit_breaker_state(self, breaker_name: str, old_state: str, 
                                 new_state: str, failure_count: int):
        """Log circuit breaker state changes."""
        logger = self.get_error_logger()
        logger.warning(
            f"Circuit breaker state change: {old_state} -> {new_state}",
            extra={
                "breaker_name": breaker_name,
                "old_state": old_state,
                "new_state": new_state,
                "failure_count": failure_count
            }
        )
    
    def log_performance_metrics(self, component: str, operation: str, 
                              duration: float, metadata: Dict[str, Any] = None):
        """Log performance metrics."""
        logger = self.get_performance_logger()
        logger.info(
            f"Performance: {operation}",
            extra={
                "component": component,
                "operation": operation,
                "duration": duration,
                "metadata": metadata or {}
            }
        )
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            "active_loggers": len(self.loggers),
            "log_directory": str(self.log_dir),
            "log_level": logging.getLevelName(self.log_level)
        }
        
        # Get log file sizes
        log_files = {}
        for log_file in self.log_dir.glob("*.log"):
            try:
                size = log_file.stat().st_size
                log_files[log_file.name] = {
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2)
                }
            except OSError:
                log_files[log_file.name] = {"error": "Could not read file"}
        
        stats["log_files"] = log_files
        return stats


# Global logger instance
diary_logger = DiaryAgentLogger()


def get_component_logger(component_name: str) -> logging.Logger:
    """Convenience function to get a component logger."""
    return diary_logger.get_logger(f"diary_agent.{component_name}", component_name)


def log_function_call(component: str):
    """Decorator to log function calls with timing."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_component_logger(component)
            start_time = datetime.now()
            
            logger.debug(
                f"Function call started: {func.__name__}",
                extra={"function": func.__name__}
            )
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.debug(
                    f"Function call completed: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "duration": duration,
                        "success": True
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(
                    f"Function call failed: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "duration": duration,
                        "success": False,
                        "error": str(e)
                    }
                )
                raise
        
        return wrapper
    return decorator