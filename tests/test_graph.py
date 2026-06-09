import os
from unittest.mock import MagicMock, patch
import pytest
from agent.graph import create_graph

@patch("agent.nodes.get_llm")
def test_graph_execution_flow(mock_get_llm, tmp_path):
    """
    Test the complete LangGraph execution, including interrupts and resumption,
    using a mocked LLM interface.
    """
    # Configure mock LLM responses
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    # First response for understand_query_node (generating pandas query)
    mock_understand_resp = MagicMock()
    mock_understand_resp.content = "df[df['age'] > 30]"
    
    # Second response for draft_response_node (drafting the answer)
    mock_draft_resp = MagicMock()
    mock_draft_resp.content = "Based on the data, the employees over 30 are Bob and Charlie."
    
    mock_llm.invoke.side_effect = [mock_understand_resp, mock_draft_resp]
    
    # Create temporary CSV file
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,age,salary\nAlice,30,60000\nBob,35,90000\nCharlie,40,80000\n")
    
    app = create_graph()
    config = {"configurable": {"thread_id": "test_run"}}
    
    inputs = {
        "csv_path": str(csv_file),
        "query": "Who is older than 30?",
        "approved": False
    }
    
    # Stream events up to the validation interrupt
    events = list(app.stream(inputs, config))
    
    # Check that execution reached expected nodes
    executed_nodes = [list(event.keys())[0] for event in events]
    assert "parse_csv" in executed_nodes
    assert "understand_query" in executed_nodes
    assert "extract_data" in executed_nodes
    assert "draft_response" in executed_nodes
    
    # The graph should now be suspended before executing human_validation node
    state = app.get_state(config)
    assert "human_validation" in state.next
    
    # Validate the data in state prior to resumption
    state_values = state.values
    assert state_values["pandas_query"] == "df[df['age'] > 30]"
    assert "Bob" in state_values["extracted_data"]
    assert "Charlie" in state_values["extracted_data"]
    assert "Alice" not in state_values["extracted_data"]
    assert "Bob and Charlie" in state_values["response"]
    
    # Simulate human approval via state update and resume execution
    app.update_state(config, {"approved": True}, as_node="human_validation")
    resume_events = list(app.stream(None, config))
    
    # Check final state and ensure execution completed
    final_state = app.get_state(config)
    assert final_state.next == ()
    assert final_state.values["approved"] is True
