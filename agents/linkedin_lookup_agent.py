# agents/linkedin_lookup_agent.py

from langchain_openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from tools.tools import get_profile_url_tavily
# Note: We are no longer using our custom callback file directly here

def lookup_agent_generator(name: str):
    """
    This is now a generator function that yields the agent's reasoning steps.
    """
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
    
    template = """given the full name {name_of_person} I want you to get me a link to their Linkedin profile page and not posts.
                              Your answer should contain only a URL"""
    prompt_template = PromptTemplate(template=template, input_variables=["name_of_person"])

    tools_for_agent = [Tool(name="Crawl Google 4 linkedin profile page", func=get_profile_url_tavily, description="useful for when you need get the Linkedin Page URL")]
    
    react_prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm=llm, tools=tools_for_agent, prompt=react_prompt)
    
    # We pass the StreamingAgentCallbackHandler directly to the executor's invoke method
    agent_executor = AgentExecutor(agent=agent, tools=tools_for_agent, handle_parsing_errors=True)
    
    # Use 'stream' instead of 'invoke' to get a real-time generator
    web_content_stream = agent_executor.stream(
        {"input": prompt_template.format_prompt(name_of_person=name)}
    )

    final_url = ""
    for chunk in web_content_stream:
        # Each 'chunk' is a dictionary containing different steps of the process
        if "actions" in chunk:
            # This is an action step
            action = chunk["actions"][0]
            yield {"type": "reasoning", "payload": f"🔎 **Action:** Using tool `{action.tool}` with input `{action.tool_input}`\n"}
        elif "steps" in chunk:
            # This is an observation step
            observation = chunk["steps"][0].observation
            yield {"type": "reasoning", "payload": f"👀 **Observation:** {observation}\n"}
        elif "output" in chunk:
            # This is the final output step
            final_url = chunk["output"]
            yield {"type": "reasoning", "payload": f"✅ **Final Answer:** {final_url}\n"}
            yield {"type": "final_url", "payload": final_url} # Yield the final URL with a specific type

    if not final_url:
        yield {"type": "error", "payload": "Could not find a LinkedIn URL."}