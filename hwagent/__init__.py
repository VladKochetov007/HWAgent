"""HWAgent - Homework Solving Agent with ReAct and MCP tools."""

from .core import ReActAgent, ReActStep
from .api import HWAgentAPI, api

__version__ = "1.0.0"
__author__ = "HWAgent Team"
__description__ = "Async ReAct agent for homework solving with MCP tools"

__all__ = ["ReActAgent", "ReActStep", "HWAgentAPI", "api"] 