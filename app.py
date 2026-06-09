import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from agent.graph import create_graph

# Setup directories
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(
    title="CSV Analyst AI Agent Web Interface",
    description="Interactive Web UI for querying CSV files with local LLM and HITL validation.",
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile graph once globally
app_workflow = create_graph()

class QueryRequest(BaseModel):
    query: str
    csv_filename: str
    thread_id: str

class ValidationRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file and return its metadata and top rows preview."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")
    
    file_path = os.path.join(DATA_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    # Parse file using pandas to verify it's clean and output details
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        preview = df.head(10).to_dict(orient="records")
        columns = list(df.columns)
        num_rows = len(df)
        num_cols = len(df.columns)
    except Exception as e:
        # Cleanup file if invalid
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Invalid or corrupted CSV format: {str(e)}")
        
    return {
        "filename": file.filename,
        "columns": columns,
        "num_rows": num_rows,
        "num_columns": num_cols,
        "preview": preview
    }

@app.post("/api/query")
async def start_query(request: QueryRequest):
    """Start the LangGraph state machine run with user input."""
    csv_path = os.path.join(DATA_DIR, request.csv_filename)
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Selected CSV file not found on server.")
        
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # Setup initial state
    inputs = {
        "csv_path": csv_path,
        "query": request.query,
        "approved": False,
    }
    
    try:
        # Run graph until it hits an interrupt (before human_validation) or ends
        for _ in app_workflow.stream(inputs, config):
            pass
            
        state = app_workflow.get_state(config)
        is_paused = "human_validation" in state.next
        values = state.values
        
        return {
            "is_paused": is_paused,
            "next_node": list(state.next),
            "state": {
                "pandas_query": values.get("pandas_query"),
                "extracted_data": values.get("extracted_data"),
                "response": values.get("response"),
                "error": values.get("error"),
                "feedback": values.get("feedback"),
                "approved": values.get("approved")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error inside LangGraph workflow: {str(e)}")

@app.post("/api/validate")
async def validate_query(request: ValidationRequest):
    """Resume the paused LangGraph workflow with user approval or feedback."""
    config = {"configurable": {"thread_id": request.thread_id}}
    
    state = app_workflow.get_state(config)
    if not state.next or "human_validation" not in state.next:
        raise HTTPException(status_code=400, detail="Graph is not currently awaiting validation.")
        
    try:
        if request.approved:
            # Set approved state in validation node context
            app_workflow.update_state(config, {"approved": True}, as_node="human_validation")
        else:
            # Submit rejection feedback to feed back into query refinement
            app_workflow.update_state(
                config, 
                {"approved": False, "feedback": request.feedback}, 
                as_node="human_validation"
            )
            
        # Resume streaming the graph
        for _ in app_workflow.stream(None, config):
            pass
            
        new_state = app_workflow.get_state(config)
        is_paused = "human_validation" in new_state.next
        values = new_state.values
        
        return {
            "is_paused": is_paused,
            "next_node": list(new_state.next),
            "state": {
                "pandas_query": values.get("pandas_query"),
                "extracted_data": values.get("extracted_data"),
                "response": values.get("response"),
                "error": values.get("error"),
                "feedback": values.get("feedback"),
                "approved": values.get("approved")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume LangGraph workflow: {str(e)}")

# Serve Static files. Must be mounted at the end so it doesn't block api routes.
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
