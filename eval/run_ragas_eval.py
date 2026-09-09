"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: eval/run_ragas_eval.py
Purpose: Automated RAG Benchmarking using Ragas (Faithfulness, Answer Relevance, Context Recall).
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

from app.agents.workflow import app_graph


async def run_evaluation():
    """
    TODO [Bài tập 1]: Triển khai script đánh giá tự động bằng Ragas:
    1. Đọc file dataset kiểm thử:
       dataset_path = Path("eval/test_dataset.json")
       with dataset_path.open(encoding="utf-8") as f:
           test_cases = json.load(f)

    2. Chạy từng câu hỏi qua đồ thị Multi-Agent `app_graph.ainvoke(...)`:
       questions = []
       answers = []
       contexts = []
       ground_truths = []

       for tc in test_cases:
           q = tc["question"]
           gt = tc["ground_truth"]
           
           # Chạy đồ thị
           initial_state = {
               "user_query": q,
               "rewritten_query": None,
               "intent": None,
               "documents": [],
               "doc_relevance": None,
               "sql_query": None,
               "sql_results": None,
               "sql_error": None,
               "sql_retry_count": 0,
               "final_response": None,
               "citations": [],
               "requires_fallback": False
           }
           final_state = await app_graph.ainvoke(initial_state)

           questions.append(q)
           answers.append(final_state.get("final_response", ""))
           # Gom context các chunks tìm được
           doc_texts = [d["content"] for d in final_state.get("documents", [])] or ["No context retrieved"]
           contexts.append(doc_texts)
           ground_truths.append(gt)

    3. Đóng gói thành HuggingFace Dataset cho Ragas:
       data = {
           "question": questions,
           "answer": answers,
           "contexts": contexts,
           "ground_truth": ground_truths
       }
       eval_dataset = Dataset.from_dict(data)

    4. Gọi hàm `evaluate(...)` của Ragas:
       results = evaluate(
           eval_dataset,
           metrics=[faithfulness, answer_relevancy, context_precision]
       )

    5. In kết quả benchmark ra màn hình:
       print("=" * 60)
       print("ENTERPRISE AGENTIC RAG (EAKP) BENCHMARK RESULTS:")
       print(results)
       print("=" * 60)
    """
    # --- BẠN HÃY TỰ ĐIỀN CODE VÀO ĐÂY ---
    pass


if __name__ == "__main__":
    asyncio.run(run_evaluation())
