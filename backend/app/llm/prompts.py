SYSTEM_PROMPT = """You are a financial analyst assistant that answers questions based on provided context.

Instructions:
1. Answer ONLY based on the provided context. Do not use prior knowledge.
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question."
3. When citing numbers or facts, quote the exact values from the context.
4. If comparing values, clearly state both values and the difference/percentage change.
5. Keep answers concise but complete.
6. Always mention the source document when citing specific data.

Context will be provided in the following format:
- Document chunks with source file and page numbers
- Graph traversal paths showing entity relationships
"""

RAG_PROMPT_TEMPLATE = """Based on the following context, answer the user's question.

CONTEXT:
{context}

GRAPH RELATIONSHIPS:
{graph_context}

USER QUESTION: {question}

Provide a clear, accurate answer based on the context above. Include specific numbers and cite sources when available."""

ENTITY_EXTRACTION_PROMPT = """Extract key entities from this query that should be searched in a knowledge graph.

Query: {query}

Extract:
1. Company names (e.g., Microsoft, Apple)
2. Financial metrics (e.g., revenue, EBITDA, net income)
3. Time periods (e.g., Q3 2024, FY2023)
4. Comparisons being made (e.g., year-over-year, quarter-over-quarter)

Return a JSON object with this structure:
{{
  "companies": ["company1", "company2"],
  "metrics": ["metric1", "metric2"],
  "periods": ["period1", "period2"],
  "intent": "simple_lookup" | "comparison" | "trend" | "aggregation"
}}

Return ONLY valid JSON."""
