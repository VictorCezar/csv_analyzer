from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes import (
    parse_csv_node,
    understand_query_node,
    extract_data_node,
    draft_response_node,
    human_validation_node,
)

def route_after_parse(state: AgentState) -> str:
    """Route to END if parsing failed, otherwise to understand_query."""
    if state.get("error"):
        return END
    return "understand_query"

def route_after_extract(state: AgentState) -> str:
    """Route back to understand_query if execution failed, otherwise to draft_response."""
    if state.get("error"):
        return "understand_query"
    return "draft_response"

def route_after_validation(state: AgentState) -> str:
    """Route to END if approved, otherwise back to understand_query with feedback."""
    if state.get("approved"):
        return END
    return "understand_query"

def create_graph():
    """
    Constructs and compiles the LangGraph workflow.
    """
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("parse_csv", parse_csv_node)
    workflow.add_node("understand_query", understand_query_node)
    workflow.add_node("extract_data", extract_data_node)
    workflow.add_node("draft_response", draft_response_node)
    workflow.add_node("human_validation", human_validation_node)
    
    # Add Edges
    workflow.add_edge(START, "parse_csv")
    
    workflow.add_conditional_edges(
        "parse_csv",
        route_after_parse,
        {
            END: END,
            "understand_query": "understand_query"
        }
    )
    
    workflow.add_edge("understand_query", "extract_data")
    
    workflow.add_conditional_edges(
        "extract_data",
        route_after_extract,
        {
            "understand_query": "understand_query",
            "draft_response": "draft_response"
        }
    )
    
    workflow.add_edge("draft_response", "human_validation")
    
    workflow.add_conditional_edges(
        "human_validation",
        route_after_validation,
        {
            END: END,
            "understand_query": "understand_query"
        }
    )
    
    # Compile with memory checkpointer and interrupt before validation
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["human_validation"])
