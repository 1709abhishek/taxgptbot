import json
from typing import List, Dict, Any
from anthropic import Anthropic

from app.config import get_settings

EXTRACTION_PROMPT = """Extract financial entities and relationships from this text.
Return valid JSON with this exact structure:

{{
  "entities": [
    {{"type": "company", "name": "Microsoft", "ticker": "MSFT"}},
    {{"type": "metric", "name": "Revenue", "value": "56.2B", "period": "Q3 2024"}},
    {{"type": "period", "name": "Q3 2024", "fiscal_year": "FY2024"}}
  ],
  "relationships": [
    {{"from": "Microsoft", "relation": "REPORTED", "to": "Revenue Q3 2024"}},
    {{"from": "Revenue Q3 2024", "relation": "INCREASED_FROM", "to": "Revenue Q3 2023"}}
  ]
}}

Entity types to extract:
- company: Company names, tickers
- metric: Financial metrics (Revenue, EBITDA, Net Income, etc.) with values and periods
- period: Time periods (Q1 2024, FY2023, etc.)
- segment: Business segments or divisions
- geography: Geographic regions

Relationship types:
- REPORTED: Company reported a metric
- HAS_METRIC: Entity has a financial metric
- FOR_PERIOD: Metric is for a time period
- INCREASED_FROM / DECREASED_FROM: Metric comparison
- PART_OF: Segment is part of company
- OPERATES_IN: Company operates in geography

Text to analyze:
{text}

Return ONLY valid JSON, no other text."""


class GraphBuilder:
    """Extract entities and relationships using Claude LLM."""

    def __init__(self):
        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def extract_entities(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract entities and relationships from chunks using Claude.
        Uses Claude Sonnet for cost efficiency during ingestion.
        """
        extractions = []

        for chunk in chunks:
            content = chunk["content"]

            # Skip very short chunks
            if len(content) < 50:
                continue

            try:
                extraction = self._extract_from_text(content)
                if extraction.get("entities") or extraction.get("relationships"):
                    extraction["source_chunk_id"] = chunk["chunk_id"]
                    extraction["source_file"] = chunk["metadata"].get("filename")
                    extractions.append(extraction)
            except Exception as e:
                # Log and continue on extraction failures
                print(f"Entity extraction failed for chunk: {e}")
                continue

        return extractions

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Use Claude to extract entities and relationships from text."""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(text=text[:4000]),  # Limit input
                }
            ],
        )

        response_text = response.content[0].text

        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        return {"entities": [], "relationships": []}
