# agents/callbacks.py

from langchain.callbacks.base import BaseCallbackHandler
from typing import Dict, Any, List
from langchain_core.outputs import LLMResult

class StreamingAgentCallbackHandler(BaseCallbackHandler):
    """
    A callback handler that yields the agent's reasoning steps in real-time.
    """
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Yield the agent's 'Thought' process."""
        thought = response.generations[0][0].text
        if 'Thought:' in thought:
            cleaned_thought = thought.split('Thought:')[1].strip()
            yield {"type": "reasoning", "payload": f"🤔 Thought: {cleaned_thought}\n"}

    def on_agent_action(self, action: Any, **kwargs: Any) -> Any:
        """Yield the agent's 'Action' and 'Action Input'."""
        log_entry = f"🔎 Action:Using tool `{action.tool}`\n   - Input: {action.tool_input}\n"
        yield {"type": "reasoning", "payload": log_entry}

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Yield the 'Observation' from a tool's execution."""
        log_entry = f"👀 Observation:\n   - {output}\n"
        yield {"type": "reasoning", "payload": log_entry}

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> Any:
        """Yield the 'Final Answer' from the agent."""
        final_answer = finish.return_values['output']
        log_entry = f"✅ Final Answer: The agent found the URL: {final_answer}\n"
        yield {"type": "reasoning", "payload": log_entry}