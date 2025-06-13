import streamlit as st
import asyncio
import os
import sys
from dotenv import load_dotenv

# It's recommended to run these pip install commands in your terminal/environment
# before running this script if the packages are not already installed.
# !python.exe -m pip install --upgrade pip
# !pip install semantic-kernel[azure] streamlit


from semantic_kernel import Kernel
from semantic_kernel.contents import ChatMessageContent

# For AI connectors
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatCompletion,
)

# For agents
from semantic_kernel.agents import (
    AzureAIAgent,
    ChatCompletionAgent,
    ChatHistoryAgentThread
)

# For Azure authentication
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool
from azure.ai.projects import AIProjectClient

# Assuming 'services.py' and 'service_settings.py' are in the grandparent_dir
# or otherwise accessible via Python's import mechanism.
# You might need to create dummy files for these if they don't exist
# or adjust the import paths if they are located elsewhere.
try:
    from services import Service
    from service_settings import ServiceSettings
except ImportError:
    # Create dummy classes if the actual modules are not available
    class Service:
        AzureOpenAI = "azureopenai"
        OpenAI = "openai"
        def __init__(self, value):
            self.value = value
        def lower(self):
            return self.value

    class ServiceSettings:
        def __init__(self):
            self.global_llm_service = os.environ.get("GLOBAL_LLM_SERVICE")


async def get_agent_response(user_input):
    """
    Sets up and runs the Semantic Kernel agents to get a response to the user's query.
    """
    load_dotenv()

    kernel = Kernel()

    service_settings = ServiceSettings()

    # Select a service to use
    selectedService = (
        Service.AzureOpenAI
        if service_settings.global_llm_service is None
        else Service(service_settings.global_llm_service.lower())
    )

    kernel.remove_all_services()

    service_id = "default"
    if selectedService == Service.OpenAI:
        kernel.add_service(
            OpenAIChatCompletion(
                service_id=service_id,
            ),
        )
    elif selectedService == Service.AzureOpenAI:
        kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
            ),
        )

    try:
        project = AzureAIAgent.create_client(
            credential=DefaultAzureCredential(),
            endpoint="https://resourceaifoundarytest.services.ai.azure.com/api/projects/firstProject"
        )

        bing_connection = await project.connections.get(name="maplehack")
        conn_id = bing_connection.id
        bing_grounding = BingGroundingTool(connection_id=conn_id)

        agent_definition = await project.agents.create_agent(
            name="BingGroundingAgent",
            instructions="Use the Bing grounding tool to answer the user's question. Add in Microsoft Build 2025 announcements and figure out how that can help as well.",
            model="gpt-4.1",
            tools=bing_grounding.definitions,
        )

        search_agent = AzureAIAgent(
            client=project,
            definition=agent_definition,
        )
    except Exception as e:
        st.error(f"Failed to initialize Azure AI Agent: {e}")
        return f"Error: Could not connect to Azure services. Please check your configuration and credentials. Details: {e}"


    # Agent definitions
    core_comps_agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="CoreComps",
        instructions="Identify and explain the core Azure services that form the backbone of a requested data or AI pattern. Explain their individual roles and how they integrate."
    )

    cost_opt_agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="CostOpt",
        instructions="Outline methods to minimize Azure consumption costs for a given data or AI pattern. This includes considerations like resource sizing, pricing tiers, reservations, auto-scaling, and data lifecycle management."
    )

    perf_opt_agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="PerfOpt",
        instructions="Detail techniques to maximize the speed and efficiency of a data or AI pattern. Address aspects such as data ingestion, processing, model inference, query performance, and caching."
    )
    
    

    azure_pattern_opt_triage_agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="agent",
        instructions=(
            "You are an expert in Azure data and AI architecture and optimization. "
            "Your task is to evaluate user requests for specific Azure data or AI patterns and forward them to the appropriate specialized agents for targeted assistance. "
            "After gathering information from the specialized agents, provide the full, comprehensive answer to the user containing all relevant information."
            "ensure to put ALL the relivant MS documentation and provide links . prioritize Microsoft Build 2025 annoucments "

            
        ),
        plugins=[
            core_comps_agent,
            cost_opt_agent,
            perf_opt_agent,
            search_agent
        ],
    )

    thread: ChatHistoryAgentThread = None

    try:
        response = await azure_pattern_opt_triage_agent.get_response(
            messages=[ChatMessageContent(role="user", content=user_input)],
            thread=thread,
        )

        if response and hasattr(response, 'message') and hasattr(response.message, 'content'):
            return response.message.content
        else:
            return f"Could not retrieve valid content from the agent's response. Full response object: {response}"
    except Exception as e:
        return f"An error occurred while getting the response from the agent: {e}"

# --- Streamlit App ---

st.title("Azure Data and AI Pattern Advisor")

st.markdown("""
Enter your query about an Azure data or AI pattern, and the agents will provide a comprehensive recommendation.
""")

user_input = st.text_area("Your Query:", "What is the best Azure pattern for data in Databricks with 300 production on-prem SQL databases that are overloaded and moving that into the cloud?", height=150)

if st.button("Get Advice"):
    if user_input:
        with st.spinner("The agents are collaborating to generate a response..."):
            # Run the async function to get the response
            response = asyncio.run(get_agent_response(user_input))
            st.markdown(response)
    else:
        st.warning("Please enter a query.")