import os
import re
import pandas as pd
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage

from agent.state import AgentState
from agent.llm import get_llm
from agent.parser import CSVParser

def clean_code(code_str: str) -> str:
    """
    Extrai de forma limpa os blocos de código markdown usando Regex,
    garantindo que qualquer texto introdutório ou saudações do LLM
    sejam descartados antes da execução no interpretador Python.
    """
    code_str = code_str.strip()
    # Try to extract code blocks using regex
    match = re.search(r"```(?:python|py)?\n(.*?)\n```", code_str, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Check if there is inline code block
    match_inline = re.search(r"```(?:python|py)?(.*?)```", code_str, re.DOTALL | re.IGNORECASE)
    if match_inline:
        return match_inline.group(1).strip()
        
    return code_str
def parse_csv_node(state: AgentState) -> Dict[str, Any]:
    """
    Node to parse CSV and construct a metadata/schema summary.
    """
    csv_path = state.get("csv_path")
    if not csv_path or not os.path.exists(csv_path):
        return {"error": f"CSV file path '{csv_path}' does not exist."}
    
    try:
        df = CSVParser.load_csv(csv_path)
        summary = CSVParser.get_summary(df)
        formatted_summary = CSVParser.format_summary_for_llm(summary)
        return {
            "csv_summary": formatted_summary,
            "error": None
        }
    except Exception as e:
        return {"error": f"Failed to parse CSV: {str(e)}"}

def understand_query_node(state: AgentState) -> Dict[str, Any]:
    """
    Node to analyze the query and generate a pandas expression to extract data.
    """
    llm = get_llm()
    query = state.get("query")
    summary = state.get("csv_summary")
    feedback = state.get("feedback")
    error = state.get("error")
    
    system_prompt = (
        "You are an expert Lead Data Scientist and Business Analyst. Your task is to write a Python script using Pandas "
        "to analyze the DataFrame 'df' and extract deep insights, correlations, statistics, or specific answers to the user's query.\n\n"
        "CRITICAL RULES:\n"
        "1. You can write multi-line Python code.\n"
        "2. You MUST store your final output in a variable named exactly `result`.\n"
        "3. Do not include markdown formatting, backticks, or explanations outside the code.\n"
        "4. ONLY use the exact column names explicitly listed in the provided 'CSV Schema'.\n"
        "5. Do NOT load or read the CSV file yourself (do NOT use `pd.read_csv`). The DataFrame `df` is already pre-loaded and available in your script's execution context. Overwriting or re-reading it will fail.\n"
        "6. If the user's query is broad or descriptive (e.g., 'what is this CSV about?', 'summarize this CSV', 'explain this dataset', or in Portuguese 'do que se trata o csv', 'resumo do dataset'), you MUST write a python script that performs a comprehensive summary of the dataset. This should include shape/size, columns/datatypes, statistical description of numeric columns (`df.describe(include='all')`), distributions of key categorical columns, and missing value counts. Store this comprehensive info in a structured dictionary/string and assign it to `result`.\n"
        "7. If the query requires complex analytical processing (e.g., finding correlations, cross-tabulations, aggregations, trend analysis, top categories, or comparative metrics), write a script that calculates all relevant metrics (such as group aggregations, correlation matrices, temporal trends, value distributions) rather than just a simple select/filter. Return all gathered data in `result`.\n"
        "8. Ensure the script handles missing data (e.g., dropna or fillna if necessary) and uses safe type conversions to avoid pandas runtime errors.\n"
        "9. CRITICAL FOR AGGREGATIONS & CORRELATIONS: When calling statistical/aggregation functions like `.mean()`, `.std()`, `.var()`, `.median()`, `.sum()`, or `.corr()`, Pandas will raise `ValueError: could not convert string to float` if there are string/object columns (such as 'Gender' with 'Female'/'Male', or 'Subscription Type' with 'Standard'). You MUST either: (a) select only numeric columns first using `df.select_dtypes(include='number')` or specifying a list of numeric columns (e.g., `df[['Age', 'Tenure']].mean()`), or (b) pass `numeric_only=True` to the aggregation function (e.g., `df.mean(numeric_only=True)` or `df.groupby('Churn').mean(numeric_only=True)`).\n\n"
        "EXAMPLES OF USAGE:\n"
        "# Example 1: General Dataset Summary (When asked what the CSV is about)\n"
        "info_summary = {\n"
        "    'total_rows': len(df),\n"
        "    'total_cols': len(df.columns),\n"
        "    'columns_and_types': df.dtypes.to_dict(),\n"
        "    'missing_values': df.isnull().sum().to_dict(),\n"
        "    'numerical_stats': df.describe(include='number').to_dict() if not df.select_dtypes(include='number').empty else {},\n"
        "    'categorical_stats': df.describe(include='object').to_dict() if not df.select_dtypes(include='object').empty else {}\n"
        "}\n"
        "result = info_summary\n\n"
        "# Example 2: Deep Business / Correlation Analysis\n"
        "numeric_df = df.select_dtypes(include='number')\n"
        "correlations = numeric_df.corr().to_dict() if not numeric_df.empty else {}\n"
        "group_metrics = df.groupby('department')[['salary']].mean().to_dict() if 'department' in df.columns and 'salary' in df.columns else {}\n"
        "result = {'correlations': correlations, 'group_metrics': group_metrics}\n"
    )
    
    user_prompt = f"CSV Schema and Structure:\n{summary}\n\nUser Query: {query}\n"
    if error:
        user_prompt += f"\nPrevious attempt failed with error: {error}. Please write a corrected, valid Pandas expression."
        if "could not convert string to float" in error:
            user_prompt += "\nTip: To fix 'could not convert string to float', ensure you only perform numeric aggregations (.mean(), .std(), .corr(), etc.) on numeric columns, or pass `numeric_only=True` to these functions."
    if feedback:
        user_prompt += f"\nHuman validator gave this feedback on the previous response: {feedback}. Adjust the Pandas expression to query the correct data."
        
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        pandas_query = clean_code(response.content)
        return {
            "pandas_query": pandas_query,
            "extracted_data": None,
            "response": None,
            "error": None,
            "feedback": None
        }
    except Exception as e:
        return {"error": f"LLM error: {str(e)}"}

def extract_data_node(state: AgentState) -> Dict[str, Any]:
    """
    Node to execute the generated pandas query safely.
    """
    csv_path = state.get("csv_path")
    pandas_query = state.get("pandas_query")
    
    if not pandas_query:
        return {"error": "No query generated by LLM."}
    
    try:
        df = CSVParser.load_csv(csv_path)
        
        # Build a safe environment for exec
        exec_globals = {"pd": pd}
        exec_locals = {"df": df}
        
        # Execute the multi-line script generated by the LLM
        try:
            exec(pandas_query, exec_globals, exec_locals)
        except Exception as e:
            try:
                exec_locals["result"] = eval(pandas_query, exec_globals, exec_locals)
            except Exception:
                raise e
        
        # Extract the mandatory 'result' variable created by the LLM's script
        if "result" not in exec_locals:
            try:
                exec_locals["result"] = eval(pandas_query, exec_globals, exec_locals)
            except Exception:
                return {"error": "The Python script did not define a 'result' variable as instructed."}
            
        result = exec_locals["result"]
        
        # Formulate string output based on type of result
        if isinstance(result, pd.DataFrame):
            extracted_str = result.to_string(index=False)
        elif isinstance(result, pd.Series):
            extracted_str = result.to_string()
        else:
            extracted_str = str(result)
            
        return {
            "extracted_data": extracted_str,
            "error": None
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}

def draft_response_node(state: AgentState) -> Dict[str, Any]:
    """
    Node to draft the final response to the user query using the extracted data.
    """
    llm = get_llm()
    query = state.get("query")
    extracted_data = state.get("extracted_data")
    
    system_prompt = (
        "You are an expert data analyst assistant. Answer the user's query using only the provided extracted data.\n"
        "Guidelines:\n"
        "1. Keep the answer clear, professional, comprehensive, and well-structured.\n"
        "2. Do not make assumptions beyond the extracted data.\n"
        "3. If the data is empty or insufficient, state that clearly.\n"
        "4. Format numerical outputs (averages, sums) nicely.\n"
        "5. ALWAYS respond in the same language as the user query (e.g. if the query is in Portuguese, write your entire response in Portuguese).\n"
        "6. If the query was general/descriptive (asking what the dataset is about) and the extracted data contains a metadata summary, write a detailed and clear explanation of the dataset: what columns exist, their data types, the main statistics (min, max, mean, count), what kind of information is stored, and highlight any interesting observations."
    )
    
    user_prompt = f"User Query: {query}\n\nExtracted Data from CSV:\n{extracted_data}\n\nAnswer:"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        return {
            "response": response.content.strip(),
            "error": None
        }
    except Exception as e:
        return {"error": f"Failed to draft response: {str(e)}"}

def human_validation_node(state: AgentState) -> Dict[str, Any]:
    """
    Placeholder node for Human-in-the-Loop validation.
    This node serves as the synchronization point.
    """
    return {}
