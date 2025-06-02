"""MCP tool for web search using LangSearch API."""

import asyncio
from typing import Any

import mcp.types as types
from mcp.server import Server

from ..utils.config import config
from ..utils.api_client import langsearch_client


async def search_web_tool(
    name: str,
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Search the web using LangSearch API.
    
    Args:
        arguments: Dictionary containing:
            - query: Search query
            - max_results: Maximum number of results (optional, defaults to config)
    """
    try:
        query = arguments.get("query")
        max_results = arguments.get("max_results")
        
        if not query:
            return [types.TextContent(
                type="text",
                text="Error: query is required"
            )]
        
        if not query.strip():
            return [types.TextContent(
                type="text",
                text="Error: query cannot be empty"
            )]
        
        # Set max_results if not provided
        if max_results is None:
            max_results = config.agent_settings["react_agent"]["web_search"]["max_results"]
        
        # Validate max_results
        if not isinstance(max_results, int) or max_results <= 0:
            return [types.TextContent(
                type="text",
                text="Error: max_results must be a positive integer"
            )]
        
        if max_results > 20:  # Reasonable limit
            max_results = 20
        
        # Perform search
        try:
            search_results = await langsearch_client.search(query, max_results)
            
            if not search_results:
                return [types.TextContent(
                    type="text",
                    text=f"No search results found for query: {query}"
                )]
            
            # Format results
            result_parts = [f"Search results for: {query}\n"]
            
            for i, result in enumerate(search_results, 1):
                title = result.get("title", "No title")
                url = result.get("url", "No URL")
                snippet = result.get("snippet", result.get("description", "No description"))
                
                result_parts.append(f"{i}. {title}")
                result_parts.append(f"   URL: {url}")
                if snippet:
                    # Limit snippet length
                    if len(snippet) > 300:
                        snippet = snippet[:300] + "..."
                    result_parts.append(f"   Description: {snippet}")
                result_parts.append("")  # Empty line between results
            
            return [types.TextContent(
                type="text",
                text="\n".join(result_parts)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error performing web search: {str(e)}"
            )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error in search_web: {str(e)}"
        )]


def register_search_web_tool(server: Server) -> None:
    """Register the search_web tool with the MCP server."""
    
    @server.call_tool()
    async def search_web(name: str, arguments: dict) -> list[types.TextContent]:
        if name != "search_web":
            raise ValueError(f"Unknown tool: {name}")
        return await search_web_tool(name, arguments)
    
    # Update server tools list
    server._tools = getattr(server, '_tools', [])
    server._tools.append(types.Tool(
        name="search_web",
        description="Search the web for information using LangSearch API",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant information"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return (optional, defaults to config setting)",
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    )) 