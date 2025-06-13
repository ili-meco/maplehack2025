# Make sure paths are correct for the imports

import os
import sys

import bing_agent

notebook_dir = os.path.abspath("")
parent_dir = os.path.dirname(notebook_dir)
grandparent_dir = os.path.dirname(parent_dir)

sys.path.append(grandparent_dir)

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,  # noqa: F401
    AzureTextCompletion,
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,  # noqa: F401
    OpenAITextCompletion,
    OpenAITextPromptExecutionSettings,  # noqa: F401
)
from semantic_kernel.contents import ChatHistory  # noqa: F401

from bing_agent import BingAgent
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.contents import ChatMessageContent, ImageContent, TextContent

from services import Service
from service_settings import ServiceSettings

service_settings = ServiceSettings()

# Select a service to use for this notebook (available services: OpenAI, AzureOpenAI, HuggingFace)
selectedService = (
    Service.AzureOpenAI
    if service_settings.global_llm_service is None
    else Service(service_settings.global_llm_service.lower())
)
print(f"Using service type: {selectedService}")

kernel = Kernel()
kernel.remove_all_services()

service_id = None
if selectedService == Service.OpenAI:
    service_id = "default"
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
        ),
    )
elif selectedService == Service.AzureOpenAI:
    service_id = "default"
    kernel.add_service(
        AzureChatCompletion(
            service_id=service_id,
        ),
    )

core_comps_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="CoreComps",  # Renamed from CoreComponentsAgent
    instructions="Identify and explain the core Azure services that form the backbone of a requested data or AI pattern. Explain their individual roles and how they integrate."
)

cost_opt_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="CostOpt",  # Renamed from CostOptimizationAgent
    instructions="Outline methods to minimize Azure consumption costs for a given data or AI pattern. This includes considerations like resource sizing, pricing tiers, reservations, auto-scaling, and data lifecycle management."
)

perf_opt_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="PerfOpt",  # Renamed from PerformanceOptimizationAgent
    instructions="Detail techniques to maximize the speed and efficiency of a data or AI pattern. Address aspects such as data ingestion, processing, model inference, query performance, and caching."
)

bing_agent = BingAgent()

azure_pattern_opt_triage_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="agent",  # Renamed from AzurePatternOptimizerTriageAgent
    instructions=(
        "You are an expert in Azure data and AI architecture and optimization. "
        "Your task is to evaluate user requests for specific Azure data or AI patterns and forward them to the appropriate specialized agents for targeted assistance. "
        "After gathering information from the specialized agents, provide the full, comprehensive answer to the user containing all relevant information."
    ),
    plugins=[
        core_comps_agent,
        cost_opt_agent,
        perf_opt_agent,
        bing_agent
    ],
)

thread = None  # type: ChatHistoryAgentThread

user_input = "what is the best azure pattern for data in databricks with 300 production on prem sql databases that are overloaded and moving that into the cloud"

import asyncio

async def main():
    response = await azure_pattern_opt_triage_agent.get_response(
        messages=user_input,
        thread=thread,
    )
    print(response.message.content)

if __name__ == "__main__":
    asyncio.run(main())