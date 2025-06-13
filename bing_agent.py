from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from semantic_kernel.agents import Agent
from pydantic import PrivateAttr

class BingAgent(Agent):
    _project: AIProjectClient = PrivateAttr()
    _agent = PrivateAttr()
    _thread = PrivateAttr()

    def __init__(self):
        super().__init__(
            name="BingSearch",
            instructions="Use Bing Search to retrieve the latest best practices for Azure architecture patterns."
        )
        self._project = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint="https://ilian-mawnpcmz-westus3.services.ai.azure.com/api/projects/ilian-mawnpcmz-westus3-project"
        )
        self._agent = self._project.agents.get_agent("asst_BuZ0yR7Q0y0rpxXYhOK4TiKT")
        self._thread = self._project.agents.threads.get("thread_Do0Jik65uZXknqq5g5rSzOFr")

    async def invoke(self, messages, **kwargs):
        # Use the latest user message as the query
        query = messages if isinstance(messages, str) else messages[-1]
        self._project.agents.messages.create(
            thread_id=self._thread.id,
            role="user",
            content=query
        )
        run = self._project.agents.runs.create_and_process(
            thread_id=self._thread.id,
            agent_id=self._agent.id
        )
        if run.status == "failed":
            return f"Run failed: {run.last_error}"
        else:
            messages = self._project.agents.messages.list(thread_id=self._thread.id, order=ListSortOrder.ASCENDING)
            for message in messages:
                if message.text_messages:
                    return message.text_messages[-1].text.value
        return "No response from Bing agent."

    async def invoke_stream(self, messages, **kwargs):
        # For now, just call invoke and yield the result
        result = await self.invoke(messages, **kwargs)
        yield result

    async def get_response(self, messages, thread=None, **kwargs):
        return await self.invoke(messages, **kwargs)