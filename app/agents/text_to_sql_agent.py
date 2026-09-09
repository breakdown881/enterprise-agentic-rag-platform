"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/agents/text_to_sql_agent.py
Purpose: Self-Healing Text-to-SQL Agent with AST Security Guardrail and Dynamic Schema Prompting.
"""

from typing import Dict, Any
from sqlalchemy import text
from langchain_core.prompts import ChatPromptTemplate
from app.agents import state
from app.agents.state import GraphState
from app.core.database import AsyncSessionLocal
from app.core.guardrails import SecurityGuardrails
from app.core.llm_gateway import LLMGateway


# =============================================================================
# 1. DATABASE SCHEMA METADATA PROMPT
# =============================================================================
DB_SCHEMA_PROMPT = """
You have access to a PostgreSQL database with the following tables:

1. users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150),
    email VARCHAR(255) UNIQUE,
    tier VARCHAR(50), -- 'STANDARD', 'VIP', 'ENTERPRISE'
    created_at TIMESTAMP WITH TIME ZONE
)

2. categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT
)

3. products (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id),
    name VARCHAR(200),
    sku VARCHAR(50) UNIQUE,
    price NUMERIC(12, 2),
    stock INT,
    created_at TIMESTAMP WITH TIME ZONE
)

4. orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    total_amount NUMERIC(12, 2),
    status VARCHAR(50), -- 'PENDING', 'COMPLETED', 'CANCELLED'
    order_date TIMESTAMP WITH TIME ZONE
)

5. order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT,
    unit_price NUMERIC(12, 2)
)

Rules:
- Generate ONLY a single, valid PostgreSQL SELECT statement.
- Do NOT wrap SQL in markdown blocks (no ```sql).
- Always use standard PostgreSQL syntax.
"""


# =============================================================================
# 2. GENERATE SQL NODE (WITH SELF-HEALING FEEDBACK)
# =============================================================================
async def generate_sql_node(state: GraphState) -> Dict[str, Any]:
    """
    TODO [Bài tập 1]: Triển khai hàm `generate_sql_node(state: GraphState)`:
    1. Lấy câu hỏi: `query = state.get("rewritten_query") or state["user_query"]`.
    2. Kiểm tra xem có lỗi từ vòng lặp trước không:
       `sql_error = state.get("sql_error")`
       `previous_sql = state.get("sql_query")`
    3. Tạo ChatPromptTemplate:
       - Nếu KHÔNG CÓ lỗi (lần đầu sinh query):
         Prompt yêu cầu dịch câu hỏi `{query}` thành câu SQL dựa trên `DB_SCHEMA_PROMPT`.
       - Nếu CÓ lỗi (Self-Healing Loop kích hoạt):
         Prompt bổ sung thông báo lỗi:
         "The previous SQL query '{previous_sql}' failed with error: '{sql_error}'. Fix the query based on the database schema."
    4. Dùng Frontier Model: `llm = LLMGateway.get_chat_model(temperature=0.0)`.
    5. Gọi model: `response = await (prompt | llm).ainvoke({"query": query})`.
    6. Làm sạch text: `clean_sql = response.content.strip().replace("```sql", "").replace("```", "").strip()`.
    7. Trả về: `{"sql_query": clean_sql}`.
    """
    query = state.get("rewritten_query") or state["user_query"]
    sql_error = state.get("sql_error")
    previous_sql = state.get("sql_query")
    
    if sql_error and previous_sql:
        system_msg = f"{DB_SCHEMA_PROMPT}\nYour previous query '{previous_sql}' failed with error: '{sql_error}'. Correct the query based on the schema."
    else:
        system_msg = f"{DB_SCHEMA_PROMPT}\nConvert the user's natural language question into a PostgreSQL SELECT query."
        
    llm = LLMGateway.get_chat_model(temperature=0.0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", "{query}")
    ])
    response = await (prompt | llm).ainvoke({"query": query})
    clean_sql = response.content.strip().replace("```sql", "").replace("```", "").strip()
    return {"sql_query": clean_sql}


# =============================================================================
# 3. EXECUTE SQL NODE (WITH AST SANITIZER)
# =============================================================================
async def execute_sql_node(state: GraphState) -> Dict[str, Any]:
    """
    TODO [Bài tập 2]: Triển khai hàm `execute_sql_node(state: GraphState)`:
    1. Lấy câu SQL và số lần retry:
       `sql = state.get("sql_query", "")`
       `retry_count = state.get("sql_retry_count", 0)`
    
    2. Chốt chặn An Ninh AST Sanitizer:
       `is_valid, sanitized_sql_or_error = SecurityGuardrails.sanitize_sql(sql)`
       Nếu `not is_valid`:
       Trả về ngay báo lỗi bảo mật và tăng retry:
       return {
           "sql_error": f"Security Guardrail Violation: {sanitized_sql_or_error}",
           "sql_retry_count": retry_count + 1
       }

    3. Thực thi an toàn trên Database qua AsyncSessionLocal():
       async with AsyncSessionLocal() as session:
           try:
               res = await session.execute(text(sanitized_sql_or_error))
               rows = [dict(row._mapping) for row in res.fetchall()]
               # Nếu thành công: xóa cờ lỗi và lưu kết quả
               return {
                   "sql_results": rows,
                   "sql_error": None
               }
           except Exception as db_err:
               # Nếu database quăng lỗi cú pháp/cột: kích hoạt Self-Healing
               return {
                   "sql_error": str(db_err),
                   "sql_retry_count": retry_count + 1
               }
    """
    
    sql = state.get("sql_query", "")
    retry_count = state.get("sql_retry_count", 0)
    is_valid, sanitized_sql_or_error = SecurityGuardrails.sanitize_sql(sql)
    if not is_valid:
        return {
            "sql_error": f"Security Guardrail Violation: {sanitized_sql_or_error}",
            "sql_retry_count": retry_count + 1
        }
    
    async with AsyncSessionLocal() as session:
        try:
            res = await session.execute(text(sanitized_sql_or_error))
            rows = [dict(row._mapping) for row in res.fetchall()]
            return {
                "sql_results": rows,
                "sql_error": None
            }
        except Exception as db_err:
            return {
                "sql_error": str(db_err),
                "sql_retry_count": retry_count + 1
            }
