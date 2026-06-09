import os
import argparse
import sys
from typing import Optional

from agent.graph import create_graph

def run_agent(csv_path: str, query: str, auto_approve: bool = False) -> Optional[str]:
    """
    Run the LangGraph CSV Analyst agent.
    
    Args:
        csv_path: Path to the input CSV file.
        query: The user query.
        auto_approve: If True, bypass the human CLI prompt and auto-approve.
        
    Returns:
        Optional[str]: The final approved response, or None if error.
    """
    app = create_graph()
    config = {"configurable": {"thread_id": "1"}}
    
    # Prepare initial state
    inputs = {
        "csv_path": csv_path,
        "query": query,
        "approved": False,
    }
    
    print("\n" + "="*50)
    print("Starting LangGraph CSV Analysis Agent...")
    print(f"CSV Path: {csv_path}")
    print(f"Query:    {query}")
    print("="*50)
    
    # Run the graph until it interrupts or finishes
    try:
        events = app.stream(inputs, config)
        for event in events:
            for node_name, state_update in event.items():
                print(f"\n[Node: {node_name}] completed.")
                if "pandas_query" in state_update and state_update["pandas_query"]:
                    print(f"  -> Generated Pandas Query: {state_update['pandas_query']}")
                if "error" in state_update and state_update["error"]:
                    print(f"  -> Error: {state_update['error']}")
                if "extracted_data" in state_update and state_update["extracted_data"]:
                    preview = state_update['extracted_data'][:150].replace('\n', ' ')
                    print(f"  -> Extracted Data (preview): {preview}...")
    except Exception as e:
        print(f"\nExecution error: {e}", file=sys.stderr)
        return None

    # CLI Loop to handle interrupts (e.g. human-in-the-loop validation)
    while True:
        state = app.get_state(config)
        
        # If there are no next nodes to execute, we have finished
        if not state.next:
            break
            
        # Handle the human_validation interrupt
        if "human_validation" in state.next:
            current_state = state.values
            print("\n" + "#"*50)
            print("HUMAN-IN-THE-LOOP VALIDATION REQUIRED")
            print("#"*50)
            print(f"CSV Summary: \n{current_state.get('csv_summary')}\n")
            print(f"Generated Pandas Query:\n  {current_state.get('pandas_query')}\n")
            print(f"Extracted Data:\n{current_state.get('extracted_data')}\n")
            print(f"Drafted Response:\n{current_state.get('response')}")
            print("#"*50 + "\n")
            
            if auto_approve or os.getenv("AUTO_APPROVE") == "true":
                print("Auto-approving response (AUTO_APPROVE set to true).")
                app.update_state(config, {"approved": True}, as_node="human_validation")
                choice = 'y'
            else:
                while True:
                    choice = input("Approve this response? [y/n]: ").strip().lower()
                    if choice in ['y', 'yes']:
                        app.update_state(config, {"approved": True}, as_node="human_validation")
                        print("\nResponse approved! Resuming graph to finish...")
                        break
                    elif choice in ['n', 'no']:
                        feedback = input("Please enter feedback/refinement instructions: ").strip()
                        app.update_state(
                            config,
                            {"approved": False, "feedback": feedback},
                            as_node="human_validation"
                        )
                        print("\nFeedback saved. Resuming graph for refinement...")
                        break
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")
            
            # Resume graph execution
            try:
                events = app.stream(None, config)
                for event in events:
                    for node_name, state_update in event.items():
                        print(f"\n[Node: {node_name}] completed.")
                        if "pandas_query" in state_update and state_update["pandas_query"]:
                            print(f"  -> Generated Pandas Query: {state_update['pandas_query']}")
                        if "error" in state_update and state_update["error"]:
                            print(f"  -> Error: {state_update['error']}")
                        if "extracted_data" in state_update and state_update["extracted_data"]:
                            preview = state_update['extracted_data'][:150].replace('\n', ' ')
                            print(f"  -> Extracted Data (preview): {preview}...")
            except Exception as e:
                print(f"\nExecution error during resume: {e}", file=sys.stderr)
                return None
                
    # Print the final output
    final_state = app.get_state(config).values
    final_response = final_state.get("response")
    print("\n" + "="*50)
    print("FINAL APPROVED RESPONSE:")
    print("="*50)
    print(final_response)
    print("="*50 + "\n")
    return final_response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modular CSV Analysis AI Agent using LangGraph & Ollama.")
    parser.add_argument("--csv", required=True, help="Path to the target CSV file")
    parser.add_argument("--query", required=True, help="Query/question to run against the CSV data")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve without human intervention")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv):
        print(f"Error: CSV file '{args.csv}' not found.", file=sys.stderr)
        sys.exit(1)
        
    run_agent(args.csv, args.query, args.auto_approve)
