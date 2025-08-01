# ice_breaker.py

from typing import Dict, Any, Generator
from dotenv import load_dotenv
from langchain.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI
from third_parties.linkedin import scrape_linkedin_profile
from agents.linkedin_lookup_agent import lookup_agent_generator
from output_parsers import summary_parser, Summary

load_dotenv()

def ice_break_with_generator(name: str) -> Generator[Dict[str, Any], None, None]:
    linkedin_profile_url = None

    
    yield {"type": "status", "payload": "Starting agent to find LinkedIn profile...\n"}

    for event in lookup_agent_generator(name=name):
        yield event
        if event.get("type") == "final_url":
            linkedin_profile_url = event["payload"]
    

    if not linkedin_profile_url or "Could not find" in linkedin_profile_url:
        yield {"type": "error", "payload": "Failed to find a valid LinkedIn profile URL. The agent could not complete the task."}
        yield {"type": "end", "payload": ""} # End the stream
        return

    try:
        yield {"type": "status", "payload": "Profile found. Scraping data and generating summary..."}
        
        # This is now a blocking call, but it happens *after* the agent's reasoning is fully streamed.
        linkedin_data = scrape_linkedin_profile(linkedin_profile_url=linkedin_profile_url)

        summary_template = """
        given the information {information} about a person from linkedin, I want you to create:
        1. A short summary
        2. two interesting facts about them
        3. A topic that may interest them
        4. 2 creative Ice breakers to open a conversation with them
        \n{format_instructions}
        """
        summary_prompt_template = PromptTemplate(
            input_variables=["information"],
            template=summary_template,
            partial_variables={"format_instructions": summary_parser.get_format_instructions()}
        )
        llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
        chain = summary_prompt_template | llm | summary_parser
        res: Summary = chain.invoke(input={"information": linkedin_data})
        
        yield {
            "type": "final_result",
            "payload": {
                "summary_and_facts": res.to_dict(),
                "picture_url": linkedin_data.get("photoUrl"),
                "sources": [linkedin_profile_url]
            }
        }
    except Exception as e:
        yield {"type": "error", "payload": f"An error occurred during scraping or summarization: {e}"}
    finally:
        # Signal that the entire process is complete.
        yield {"type": "end", "payload": "Process finished."}