import json
import re
from openai import OpenAI
from dataclasses import dataclass
from typing import Any

# Assuming tool_manager.py is in the same directory or accessible via python path
from .tool_manager import ToolManager 

@dataclass
class ParsedLLMResponse:
    thought: str | None = None
    plan: list[str] | None = None
    tool_call_name: str | None = None # From text-based parsing, for warning or fallback
    tool_call_params: dict[str, Any] | None = None # From text-based parsing
    final_answer: str | None = None
    raw_text: str = ""

class ReActAgent:
    MAX_ITERATIONS = 7 # Increased slightly to allow for more complex multi-step tasks

    def __init__(self, client: OpenAI, model_name: str, tool_manager: ToolManager, base_system_prompt: str, agent_prompts: dict):
        self.client = client
        self.model_name = model_name
        self.tool_manager = tool_manager
        self.base_system_prompt = base_system_prompt.strip()
        self.conversation_history: list[dict[str, Any]] = [] # Can hold more complex dicts now
        self.messages = agent_prompts # From prompts.yaml agent_messages.react_agent
        self.parser_msgs = self.messages.get("parser", {})

    def _construct_full_system_prompt(self) -> str:
        tool_defs_for_text_prompt = self.tool_manager.get_tool_definitions_for_prompt() # For the text part of system prompt
        base_addition_template = self.messages.get("base_system_prompt_addition", "")
        # Note: The actual tool definitions for the API are passed in the 'tools' parameter of the API call.
        # The TOOL_DEFINITIONS here is for the LLM's textual understanding and ReAct formatting.
        return f"""{self.base_system_prompt}
{base_addition_template.format(tool_defs=tool_defs_for_text_prompt)}
"""

    def _parse_llm_response(self, response_text: str) -> ParsedLLMResponse:
        parsed = ParsedLLMResponse(raw_text=response_text)

        thought_match = re.search(r"THOUGHT:(.*?)(PLAN:|TOOL_CALL:|FINAL_ANSWER:|$)", response_text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            parsed.thought = thought_match.group(1).strip()

        plan_match = re.search(r"PLAN:(.*?)(TOOL_CALL:|FINAL_ANSWER:|$)", response_text, re.DOTALL | re.IGNORECASE)
        if plan_match:
            plan_text = plan_match.group(1).strip()
            parsed.plan = [step.strip() for step in re.findall(r"^\d+\.\s*(.*)", plan_text, re.MULTILINE)]

        tool_call_marker_str = "TOOL_CALL:"
        temp_response_text_upper = response_text.upper()
        tool_call_marker_pos = temp_response_text_upper.find(tool_call_marker_str)
        tool_call_parsed_successfully = False

        if tool_call_marker_pos != -1:
            search_for_brace_start_pos = tool_call_marker_pos + len(tool_call_marker_str)
            first_brace_pos_in_suffix = -1
            for i in range(search_for_brace_start_pos, len(response_text)):
                if response_text[i] == '{':
                    first_brace_pos_in_suffix = i
                    break
                elif not response_text[i].isspace():
                    break
            
            if first_brace_pos_in_suffix != -1:
                json_text_segment_to_decode = response_text[first_brace_pos_in_suffix:]
                decoder = json.JSONDecoder()
                try:
                    tool_call_data, _ = decoder.raw_decode(json_text_segment_to_decode)
                    parsed.tool_call_name = tool_call_data.get("tool_name")
                    parsed.tool_call_params = tool_call_data.get("parameters")
                    tool_call_parsed_successfully = True # Parsed from text
                    if not parsed.tool_call_name:
                        msg = self.parser_msgs.get("tool_call_missing_name_warning", "")
                        print(f"Warning: {msg}")
                        parsed.thought = (parsed.thought + "\n" if parsed.thought else "") + msg
                        tool_call_parsed_successfully = False
                except json.JSONDecodeError as e:
                    err_msg_template = self.parser_msgs.get("tool_call_json_decode_error_warning", "")
                    err_msg = err_msg_template.format(error=e, segment=json_text_segment_to_decode[:100].strip())
                    print(f"Warning: {err_msg}")
                    parsed.thought = (parsed.thought + "\n" if parsed.thought else "") + f"[System Error: {err_msg}]"
            else:
                err_msg = self.parser_msgs.get("tool_call_no_brace_warning", "")
                print(f"Warning: {err_msg}")
                parsed.thought = (parsed.thought + "\n" if parsed.thought else "") + f"[System Error: {err_msg}]"

        if not tool_call_parsed_successfully: # Only look for FINAL_ANSWER if no text-based tool call was parsed
            final_answer_marker_str = "FINAL_ANSWER:"
            final_answer_marker_pos = temp_response_text_upper.rfind(final_answer_marker_str)
            if final_answer_marker_pos != -1:
                is_part_of_thought = parsed.thought and final_answer_marker_str in parsed.thought.upper()
                is_part_of_plan = False
                if parsed.plan:
                    for p_step in parsed.plan:
                        if final_answer_marker_str in p_step.upper():
                            is_part_of_plan = True
                            break
                if not (is_part_of_thought or is_part_of_plan):
                    final_answer_start_pos = final_answer_marker_pos + len(final_answer_marker_str)
                    parsed.final_answer = response_text[final_answer_start_pos:].strip()
        
        if tool_call_parsed_successfully:
             parsed.final_answer = None # Ensure no final answer if a text tool call was parsed

        return parsed

    def process_user_request(self, user_input: str) -> str:
        full_system_prompt = self._construct_full_system_prompt()
        self.conversation_history = [{"role": "system", "content": full_system_prompt}]
        self.conversation_history.append({"role": "user", "content": user_input})

        tools_for_api = self.tool_manager.get_tools_for_api()

        for iteration in range(self.MAX_ITERATIONS):
            print(f"--- Agent Iteration {iteration + 1} ---")
            try:
                completion_params: dict[str, Any] = {
                    "model": self.model_name,
                    "messages": self.conversation_history,
                }
                if tools_for_api:
                    completion_params["tools"] = tools_for_api
                    completion_params["tool_choice"] = "auto" # Explicitly set to auto

                completion = self.client.chat.completions.create(**completion_params)

                if not (completion.choices and completion.choices[0].message):
                    error_msg = self.messages.get("failed_to_get_model_response_error", "")
                    self.conversation_history.append({"role": "assistant", "content": f"[System Error: {error_msg}]"})
                    return error_msg

                assistant_message_obj = completion.choices[0].message
                self.conversation_history.append(assistant_message_obj.model_dump(exclude_none=True))

                assistant_response_text_content = assistant_message_obj.content or ""
                print(f"LLM Raw Output (text part):\n{assistant_response_text_content}")
                if assistant_message_obj.tool_calls:
                    print(f"LLM Tool Calls (structured): {assistant_message_obj.tool_calls}")
                
                parsed_text_parts = self._parse_llm_response(assistant_response_text_content)

                if parsed_text_parts.thought:
                    print(f"THOUGHT: {parsed_text_parts.thought}")
                if parsed_text_parts.plan:
                    print(f"PLAN: {parsed_text_parts.plan}")

                if assistant_message_obj.tool_calls:
                    for tool_call_api_obj in assistant_message_obj.tool_calls:
                        tool_call_id = tool_call_api_obj.id
                        tool_name_from_api = tool_call_api_obj.function.name
                        tool_params_str_from_api = tool_call_api_obj.function.arguments
                        print(f"Executing API Tool Call: ID={tool_call_id}, Name={tool_name_from_api}, Args='{tool_params_str_from_api}'")
                        try:
                            tool_params_dict = json.loads(tool_params_str_from_api)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding tool arguments JSON: {e}")
                            tool_output_content = self.messages.get("failed_to_parse_tool_args_error", "").format(tool_name=tool_name_from_api, error=e, args=tool_params_str_from_api)
                            self.conversation_history.append({"role": "tool", "tool_call_id": tool_call_id, "name": tool_name_from_api, "content": tool_output_content})
                            continue
                        
                        raw_tool_output = self.tool_manager.execute_tool(tool_name_from_api, tool_params_dict)
                        print(f"Raw TOOL_OUTPUT from manager: {raw_tool_output}")
                        formatted_tool_output_content: str
                        if raw_tool_output.lower().startswith("error:"):
                            error_detail = raw_tool_output[len('error:'):].strip()
                            formatted_tool_output_content = f"*error while calling tool: {error_detail}*"
                        else:
                            formatted_tool_output_content = raw_tool_output
                        print(f"Formatted TOOL_OUTPUT for history: {formatted_tool_output_content}")
                        self.conversation_history.append({"role": "tool", "tool_call_id": tool_call_id, "name": tool_name_from_api, "content": formatted_tool_output_content})
                
                elif parsed_text_parts.tool_call_name and parsed_text_parts.tool_call_params is not None: # Text-based tool call detected
                    warning_msg_template = self.messages.get("text_tool_call_warning", "")
                    warning_msg = warning_msg_template.format(tool_name=parsed_text_parts.tool_call_name)
                    print(warning_msg)
                    error_content_for_llm_template = self.messages.get("text_tool_call_system_note", "")
                    error_content_for_llm = error_content_for_llm_template.format(tool_name=parsed_text_parts.tool_call_name)
                    self.conversation_history.append({"role": "assistant", "content": error_content_for_llm})
                
                elif parsed_text_parts.final_answer:
                    print(f"FINAL_ANSWER: {parsed_text_parts.final_answer}")
                    return parsed_text_parts.final_answer
                
                elif assistant_response_text_content.strip(): # LLM provided text, but no API tool call, no text tool call, no final answer
                    print(self.messages.get("bot_text_but_no_action_note", ""))
                
                else: # Empty response from LLM
                    no_action_msg = self.messages.get("model_empty_response_note", "")
                    print(no_action_msg)
                    self.conversation_history.append({"role": "assistant", "content": self.messages.get("model_empty_response_system_note", "")})
                    return no_action_msg

            except Exception as e:
                error_msg_template = self.messages.get("agent_processing_error", "")
                error_msg = error_msg_template.format(error=str(e))
                print(error_msg)
                self.conversation_history.append({"role": "assistant", "content": f"[System Error: {error_msg}]"})
                return error_msg

        max_iter_msg = self.messages.get("max_iterations_reached_message", "")
        print(max_iter_msg)
        self.conversation_history.append({"role": "assistant", "content": max_iter_msg})
        return max_iter_msg 