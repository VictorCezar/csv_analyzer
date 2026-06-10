from typing import TypedDict, Optional

class AgentState(TypedDict):
    """
    State representing the agent's memory and current context during workflow execution.
    """
    csv_path: str
    query: str
    csv_summary: Optional[str]
    pandas_query: Optional[str]
    extracted_data: Optional[str]
    response: Optional[str]
    approved: bool
    feedback: Optional[str]
    error: Optional[str]
    retry_count: Optional[int]

