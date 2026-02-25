SYSTEM_PROMPT = """You are a helpful financial analyst assistant. Your job is to answer questions using the provided context.

CRITICAL INSTRUCTIONS:
1. ALWAYS provide an answer if the context contains relevant information. Do NOT say "I don't have enough information" unless the context is completely unrelated.
2. Extract and synthesize information from the context to form comprehensive answers.
3. When you see definitions, explanations, or descriptions in the context, use them to answer definitional questions.
4. When you see lists, breakdowns, or categories in the context, include them in your answer.
5. When citing numbers or facts, quote the exact values and mention the source.
6. For tax form questions, explain what you find in the context about the forms.
7. Keep answers concise but complete.

Remember: The context provided IS the answer source. Use it!
"""

RAG_PROMPT_TEMPLATE = """Based on the following context, answer the user's question.

CONTEXT:
{context}

GRAPH RELATIONSHIPS:
{graph_context}

USER QUESTION: {question}

Instructions:
- Provide a clear, accurate answer using the context above
- Include specific numbers, percentages, and counts when available
- Cite the source document for your information
- If the context contains lists or breakdowns, include them in your answer
- Extract and summarize relevant information even if it's not a perfect match"""

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
