# Make sure paths are correct for the imports

import os
import sys
import base64
import requests
from dotenv import load_dotenv

import bing_agent

# Load environment variables for GPT-4o image-to-text
load_dotenv()
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME").replace('"', '')

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
    print("Welcome to the Azure Architecture Conversational Agent!")
    print("You can ask questions or provide an image file path to analyze an architecture diagram.")
    print("Type 'exit' to quit.\n")
    print("Tip: You can upload an image by pasting its file path, or ask follow-up questions about previous answers.")
    conversation_history = []
    global user_input
    while True:
        user_message = input("You: ")
        if user_message.strip().lower() == "exit":
            print("Goodbye!")
            break
        # Check if the user message contains a file path (even if mixed with text)
        file_path = None
        for part in user_message.split():
            if os.path.isfile(part):
                file_path = part
                break
        if file_path:
            print(f"Extracting text from image: {file_path}")
            try:
                extracted_text = image_to_text_gpt4o(file_path)
                print("Extracted text:", extracted_text)
                # Combine user message (minus file path) and extracted text for context
                user_input = user_message.replace(file_path, "").strip() + "\n[Diagram Analysis]: " + extracted_text
                # Use the triage/orchestrator agent for orchestration
                response = await azure_pattern_opt_triage_agent.get_response(
                    messages=user_input,
                    thread=thread,
                )
                print("Agent:", response.message.content)
                print("\nWould you like to go deeper on any topic, see a sample template, or upload an architecture diagram?\n")
            except Exception as e:
                print(f"Error extracting text from image: {e}")
                continue
        else:
            user_input = user_message
        conversation_history.append({"role": "user", "content": user_input})
        try:
            response = await azure_pattern_opt_triage_agent.get_response(
                messages=[msg["content"] for msg in conversation_history],
                thread=thread,
            )
            conversation_history.append({"role": "agent", "content": response.message.content})
            print("Agent:", response.message.content)
            print("\nWould you like to go deeper on any topic, see a sample template, or upload an architecture diagram?\n")
        except Exception as e:
            print(f"Agent error: {e}")

def image_to_text_gpt4o(image_path):
    """
    Uses Azure OpenAI GPT-4o Vision to extract text from an image.
    """
    endpoint = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_CHAT_DEPLOYMENT_NAME}/chat/completions?api-version=2024-02-15-preview"
    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    data = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this architecture diagram in detail."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            }
        ],
        "max_tokens": 1024
    }
    response = requests.post(endpoint, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]

if __name__ == "__main__":
    asyncio.run(main())