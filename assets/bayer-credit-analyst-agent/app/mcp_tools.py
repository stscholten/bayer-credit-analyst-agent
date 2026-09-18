"""
MCP tools indirection layer — re-exports get_mcp_tools from the provider.
This module exists so that .coveragerc and tests can reference it cleanly.
"""
from mcp_providers.agw import get_mcp_tools

__all__ = ["get_mcp_tools"]
