import os
import sys
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from agent.llm import get_llm, get_embeddings
from agent.graph import create_graph

def run_evaluation() -> None:
    """
    Load validation questions, generate agent predictions, and run Ragas evaluation.
    """
    csv_path = "data/sample.csv"
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found. Please run this script from the project root.", file=sys.stderr)
        sys.exit(1)
        
    eval_data = [
        {
            "question": "What is the average salary of Engineering department employees?",
            "ground_truth": "The average salary of Engineering employees is $93,333.33."
        },
        {
            "question": "Who is the oldest employee in the dataset and what is their department?",
            "ground_truth": "George is the oldest employee at 45 years old, and he is in the Engineering department."
        },
        {
            "question": "How many employees work in HR?",
            "ground_truth": "There are 2 employees working in the HR department."
        }
    ]
    
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    # Enable auto-approval for the evaluation run
    os.environ["AUTO_APPROVE"] = "true"
    app = create_graph()
    
    print("\n" + "="*50)
    print("GENERATING AGENT ANSWERS FOR EVALUATION")
    print("="*50)
    
    for i, item in enumerate(eval_data, 1):
        query = item["question"]
        print(f"\n[{i}/{len(eval_data)}] Query: '{query}'")
        
        config = {"configurable": {"thread_id": f"eval_run_{i}"}}
        inputs = {
            "csv_path": csv_path,
            "query": query,
            "approved": True  # auto-approve
        }
        
        try:
            # Stream/run the graph
            for event in app.stream(inputs, config):
                pass
                
            state = app.get_state(config)
            final_values = state.values
            
            response = final_values.get("response", "No response generated.")
            extracted_data = final_values.get("extracted_data", "")
            csv_summary = final_values.get("csv_summary", "")
            
            # Format context as a list of strings
            context_list = [extracted_data] if extracted_data else [csv_summary]
            
            questions.append(query)
            answers.append(response)
            contexts.append(context_list)
            ground_truths.append(item["ground_truth"])
            
            print(f"  -> Answer: {response}")
            print(f"  -> Context: {context_list[0][:100]}...")
        except Exception as e:
            print(f"  -> Error executing query: {e}", file=sys.stderr)
            
    print("\n" + "="*50)
    print("RUNNING RAGAS LOCAL EVALUATION")
    print("="*50)
    
    if not questions:
        print("Error: No successful runs to evaluate.", file=sys.stderr)
        sys.exit(1)
        
    # Build Dataset for Ragas
    eval_dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })
    
    # Initialize local Ollama models
    try:
        local_llm = get_llm(temperature=0.0)
        local_embeddings = get_embeddings()
        
        ragas_llm = LangchainLLMWrapper(local_llm)
        ragas_embeddings = LangchainEmbeddingsWrapper(local_embeddings)
        
        # Link metrics to our local wrappers
        faithfulness.llm = ragas_llm
        answer_relevance.llm = ragas_llm
        answer_relevance.embeddings = ragas_embeddings
        
        print("Evaluating dataset via Ragas with local Ollama models...")
        result = evaluate(
            dataset=eval_dataset,
            metrics=[faithfulness, answer_relevance],
            llm=ragas_llm,
            embeddings=ragas_embeddings
        )
        
        print("\n" + "="*50)
        print("EVALUATION METRIC SCORES:")
        print("="*50)
        for metric, score in result.items():
            print(f"{metric:<25} : {score:.4f}")
        print("="*50)
        
        # Convert results to dataframe and save
        result_df = result.to_pandas()
        output_csv = "evaluation_results.csv"
        result_df.to_csv(output_csv, index=False)
        print(f"\nDetailed evaluation results saved to '{output_csv}'")
        
    except Exception as e:
        print(f"\nEvaluation scoring failed: {e}", file=sys.stderr)
        print("\nExtracted Dataset for reference:")
        for idx in range(len(questions)):
            print(f"\nQuestion: {questions[idx]}")
            print(f"Answer: {answers[idx]}")
            print(f"Context: {contexts[idx]}")
            print(f"Ground Truth: {ground_truths[idx]}")

if __name__ == "__main__":
    run_evaluation()
