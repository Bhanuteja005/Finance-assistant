import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with both file and console handlers."""
    
    # Create logs directory if it doesn't exist
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create application loggers
main_logger = setup_logger("finance_assistant", "logs/main.log")
agent_logger = setup_logger("agents", "logs/agents.log")
data_logger = setup_logger("data_pipeline", "logs/data.log")
