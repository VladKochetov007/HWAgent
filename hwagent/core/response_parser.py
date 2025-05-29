"""
LLM Response Parser for ReAct format.
Following Single Responsibility Principle - handles only response parsing.
"""

import json
import re
from typing import Any
from hwagent.core.models import ParsedLLMResponse
from hwagent.core.message_manager import MessageManager
from hwagent.core.agent_config import get_agent_config


class ResponseParser:
    """Parses LLM responses in ReAct format."""
    
    def __init__(self, message_manager: MessageManager):
        """
        Initialize ResponseParser.
        
        Args:
            message_manager: Message manager for error messages
        """
        self.message_manager = message_manager
    
    def parse_llm_response(self, response_text: str) -> ParsedLLMResponse:
        """
        Parse LLM response text into structured format.
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            ParsedLLMResponse object with extracted components
        """
        agent_config = get_agent_config()
        debug_enabled = agent_config.is_debug_enabled()
        verbose_parsing = agent_config.is_verbose_parsing_enabled()
        
        if debug_enabled and verbose_parsing:
            print(f"[DEBUG] ResponseParser: Parsing LLM response of length {len(response_text)}")
            print(f"[DEBUG] ResponseParser: Response preview: {repr(response_text[:200])}")
        
        parsed = ParsedLLMResponse(raw_text=response_text)
        
        # Parse each component
        parsed.thought = self._extract_thought(response_text)
        if debug_enabled and verbose_parsing:
            print(f"[DEBUG] ResponseParser: Extracted thought: {repr(parsed.thought[:100] if parsed.thought else None)}")
        
        parsed.plan = self._extract_plan(response_text)
        if debug_enabled and verbose_parsing:
            print(f"[DEBUG] ResponseParser: Extracted plan: {parsed.plan}")
        
        # Parse tool call and final answer (mutually exclusive)
        tool_call_parsed = self._extract_tool_call(response_text, parsed)
        if debug_enabled and verbose_parsing:
            print(f"[DEBUG] ResponseParser: Tool call parsed: {tool_call_parsed}")
            if tool_call_parsed:
                print(f"[DEBUG] ResponseParser: Tool name: {parsed.tool_call_name}, params: {parsed.tool_call_params}")
        
        if not tool_call_parsed:
            parsed.final_answer = self._extract_final_answer(response_text, parsed)
            if debug_enabled and verbose_parsing:
                print(f"[DEBUG] ResponseParser: Final answer: {repr(parsed.final_answer[:100] if parsed.final_answer else None)}")
        else:
            parsed.final_answer = None  # Ensure no final answer if tool call was parsed
        
        if debug_enabled and verbose_parsing:
            print(f"[DEBUG] ResponseParser: Parsing complete. Has tool call: {parsed.has_tool_call()}, Has final answer: {parsed.has_final_answer()}")
        
        return parsed
    
    def _extract_thought(self, response_text: str) -> str | None:
        """Extract THOUGHT section from response."""
        thought_pattern = r"THOUGHT:(.*?)(PLAN:|TOOL_CALL:|FINAL_ANSWER:|$)"
        match = re.search(thought_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_plan(self, response_text: str) -> list[str] | None:
        """Extract PLAN section from response."""
        plan_pattern = r"PLAN:(.*?)(TOOL_CALL:|FINAL_ANSWER:|$)"
        match = re.search(plan_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            plan_text = match.group(1).strip()
            # Extract numbered steps
            steps = re.findall(r"^\d+\.\s*(.*)", plan_text, re.MULTILINE)
            return [step.strip() for step in steps] if steps else None
        return None
    
    def _extract_tool_call(self, response_text: str, parsed: ParsedLLMResponse) -> bool:
        """
        Extract TOOL_CALL section from response.
        
        Args:
            response_text: Raw response text
            parsed: ParsedLLMResponse object to update with errors
            
        Returns:
            True if tool call was successfully parsed, False otherwise
        """
        tool_call_marker = "TOOL_CALL:"
        response_upper = response_text.upper()
        marker_pos = response_upper.find(tool_call_marker)
        
        if marker_pos == -1:
            return False
        
        # Find JSON object after marker
        json_start_pos = self._find_json_start(response_text, marker_pos + len(tool_call_marker))
        
        if json_start_pos == -1:
            error_msg = self.message_manager.get_nested_message(
                "react_agent", "parser", "tool_call_no_brace_warning"
            )
            self._add_error_to_thought(parsed, error_msg)
            return False
        
        # Parse JSON
        json_segment = response_text[json_start_pos:]
        return self._parse_tool_call_json(json_segment, parsed)
    
    def _find_json_start(self, response_text: str, search_start: int) -> int:
        """Find the start position of JSON object."""
        for i in range(search_start, len(response_text)):
            if response_text[i] == '{':
                return i
            elif not response_text[i].isspace():
                break
        return -1
    
    def _parse_tool_call_json(self, json_segment: str, parsed: ParsedLLMResponse) -> bool:
        """
        Parse tool call JSON data.
        
        Args:
            json_segment: JSON string segment
            parsed: ParsedLLMResponse object to update
            
        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            decoder = json.JSONDecoder()
            tool_call_data, _ = decoder.raw_decode(json_segment)
            
            parsed.tool_call_name = tool_call_data.get("tool_name")
            parsed.tool_call_params = tool_call_data.get("parameters")
            
            if not parsed.tool_call_name:
                error_msg = self.message_manager.get_nested_message(
                    "react_agent", "parser", "tool_call_missing_name_warning"
                )
                self._add_error_to_thought(parsed, error_msg)
                return False
            
            return True
            
        except json.JSONDecodeError as e:
            error_msg = self.message_manager.format_nested_message(
                "react_agent", "parser", "tool_call_json_decode_error_warning",
                error=e, segment=json_segment[:100].strip()
            )
            self._add_error_to_thought(parsed, f"[System Error: {error_msg}]")
            return False
    
    def _extract_final_answer(self, response_text: str, parsed: ParsedLLMResponse) -> str | None:
        """Extract FINAL_ANSWER section from response."""
        final_answer_marker = "FINAL_ANSWER:"
        response_upper = response_text.upper()
        marker_pos = response_upper.rfind(final_answer_marker)
        
        if marker_pos == -1:
            return None
        
        # Check if marker is part of thought or plan
        if self._is_marker_in_section(final_answer_marker, parsed.thought, parsed.plan):
            return None
        
        # Extract final answer
        answer_start = marker_pos + len(final_answer_marker)
        return response_text[answer_start:].strip()
    
    def _is_marker_in_section(self, marker: str, thought: str | None, plan: list[str] | None) -> bool:
        """Check if marker appears in thought or plan sections."""
        # Check thought section
        if thought and marker in thought.upper():
            return True
        
        # Check plan section
        if plan:
            for step in plan:
                if marker in step.upper():
                    return True
        
        return False
    
    def _add_error_to_thought(self, parsed: ParsedLLMResponse, error_msg: str) -> None:
        """Add error message to thought section."""
        if parsed.thought:
            parsed.thought += f"\n{error_msg}"
        else:
            parsed.thought = error_msg
        
        # Also print warning
        print(f"Warning: {error_msg}") 