"""
Web Search Tool - performs web search using LangSearch API.
Follows SOLID principles and uses core components.
"""

import os
import json
from typing import Any
import requests

from hwagent.core import (
    BaseTool, ToolExecutionResult, Constants, 
    ParameterValidator, ValidationError
)


class WebSearchService:
    """Handles web search API requests. Following SRP."""
    
    def __init__(self):
        self.api_url = Constants.LANGSEARCH_API_URL
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> str:
        """Get LangSearch API key from environment variables."""
        api_key = os.getenv(Constants.LANGSEARCH_API_KEY)
        if not api_key:
            raise ValidationError(
                "LangSearch API key not found",
                f"Please set {Constants.LANGSEARCH_API_KEY} environment variable"
            )
        return api_key
    
    def search(self, query: str, count: int = Constants.DEFAULT_SEARCH_COUNT, 
               freshness: str = Constants.FRESHNESS_NO_LIMIT, 
               summary: bool = True) -> dict[str, Any]:
        """Perform web search using LangSearch API."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "query": query,
            "freshness": freshness,
            "summary": summary,
            "count": count
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Web search API request failed", str(e))
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid API response format", str(e))


class SearchResultFormatter:
    """Formats search results for display. Following SRP."""
    
    @staticmethod
    def format_search_results(api_response: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Format API response into readable text and metadata."""
        try:
            data = api_response.get('data', {})
            web_pages = data.get('webPages', {})
            results = web_pages.get('value', [])
            query_context = data.get('queryContext', {})
            original_query = query_context.get('originalQuery', '')
            
            if not results:
                return "No search results found.", {"query": original_query, "count": 0}
            
            # Format results
            formatted_lines = [
                f"🔍 Search results for: '{original_query}'",
                f"📊 Found {len(results)} results:",
                ""
            ]
            
            for i, result in enumerate(results, 1):
                name = result.get('name', 'Untitled')
                url = result.get('url', '')
                snippet = result.get('snippet', '')
                summary = result.get('summary', '')
                date_published = result.get('datePublished', '')
                
                formatted_lines.extend([
                    f"{i}. **{name}**",
                    f"   🌐 URL: {url}",
                ])
                
                if date_published:
                    formatted_lines.append(f"   📅 Published: {date_published}")
                
                if snippet:
                    # Limit snippet length for readability
                    snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet
                    formatted_lines.append(f"   📝 Snippet: {snippet}")
                
                if summary and summary != snippet:
                    # Limit summary length
                    summary = summary[:500] + "..." if len(summary) > 500 else summary
                    formatted_lines.append(f"   📋 Summary: {summary}")
                
                formatted_lines.append("")  # Empty line between results
            
            formatted_text = "\n".join(formatted_lines)
            
            metadata = {
                "query": original_query,
                "count": len(results),
                "results": results,
                "total_estimated": web_pages.get('totalEstimatedMatches'),
                "some_results_removed": web_pages.get('someResultsRemoved', False)
            }
            
            return formatted_text, metadata
            
        except (KeyError, TypeError) as e:
            raise ValidationError(f"Error formatting search results", str(e))


class WebSearchTool(BaseTool):
    """Tool for performing web searches using LangSearch API."""
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        self.search_service = WebSearchService()
        self.formatter = SearchResultFormatter()
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for information on any topic and get detailed results with summaries"
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "The search query to find information about"
            },
            "count": {
                "type": "integer",
                "description": f"Number of search results to return (1-{Constants.MAX_SEARCH_COUNT}, default: {Constants.DEFAULT_SEARCH_COUNT})",
                "default": Constants.DEFAULT_SEARCH_COUNT
            },
            "freshness": {
                "type": "string",
                "description": f"Time range for search results. Options: {Constants.FRESHNESS_ONE_DAY}, {Constants.FRESHNESS_ONE_WEEK}, {Constants.FRESHNESS_ONE_MONTH}, {Constants.FRESHNESS_ONE_YEAR}, {Constants.FRESHNESS_NO_LIMIT} (default)",
                "default": Constants.FRESHNESS_NO_LIMIT
            },
            "summary": {
                "type": "boolean",
                "description": "Whether to include detailed summaries in results (default: true)",
                "default": True
            }
        }
    
    def validate_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Validate web search parameters."""
        # Validate base parameters
        base_result = super().validate_parameters(parameters)
        if base_result.is_error():
            return base_result
        
        # Validate query parameter (required)
        query = parameters.get("query")
        query_result = ParameterValidator.validate_required_string(query, "query")
        if query_result.is_error():
            return query_result
        
        # Validate count parameter (optional)
        count = parameters.get("count", Constants.DEFAULT_SEARCH_COUNT)
        if count is not None:
            count_result = ParameterValidator.validate_search_count(count)
            if count_result.is_error():
                return count_result
        
        # Validate freshness parameter (optional)
        freshness = parameters.get("freshness", Constants.FRESHNESS_NO_LIMIT)
        if freshness is not None:
            freshness_result = ParameterValidator.validate_freshness_parameter(freshness)
            if freshness_result.is_error():
                return freshness_result
        
        # Validate summary parameter (optional)
        summary = parameters.get("summary", True)
        if summary is not None and not isinstance(summary, bool):
            return ToolExecutionResult.error(
                "Parameter 'summary' must be a boolean",
                f"Got: {type(summary).__name__}"
            )
        
        return ToolExecutionResult.success("All parameters validated successfully")
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Execute web search."""
        query = kwargs["query"]
        count = kwargs.get("count", Constants.DEFAULT_SEARCH_COUNT)
        freshness = kwargs.get("freshness", Constants.FRESHNESS_NO_LIMIT)
        summary = kwargs.get("summary", True)
        
        try:
            # Perform search
            api_response = self.search_service.search(
                query=query,
                count=count,
                freshness=freshness,
                summary=summary
            )
            
            # Format results
            formatted_text, metadata = self.formatter.format_search_results(api_response)
            
            return ToolExecutionResult.success(
                f"web search completed for query: '{query}'",
                formatted_text,
                data=metadata
            )
            
        except ValidationError as e:
            return ToolExecutionResult.error(
                f"web search failed for query: '{query}'",
                f"{e.message}: {e.details}" if e.details else e.message
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"web search failed for query: '{query}'",
                f"Unexpected error: {str(e)}"
            ) 