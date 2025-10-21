"""
Multi-Agent E-commerce System

A comprehensive AI-powered multi-agent system for warehouse and marketplace integration.
"""

__version__ = "1.0.0"
__author__ = "Multi-Agent Team"
__email__ = "team@multiagent.com"

from .shared.base_agent import BaseAgent
from .shared.models import *
from .shared.database import DatabaseManager

__all__ = [
    "BaseAgent",
    "DatabaseManager",
    "__version__",
]
