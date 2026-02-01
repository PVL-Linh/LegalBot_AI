from typing import Annotated, Sequence, TypedDict, Union
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # The 'messages' key is required for most LangGraph setups
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # 'summary' stores a condensed version of the conversation so far
    summary: str
    # 'pdf_context' stores text extracted from uploaded documents for the current session
    pdf_context: str
