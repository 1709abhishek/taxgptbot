import io
from typing import List, Dict, Any
import pandas as pd

from .base import BaseParser


class CSVParser(BaseParser):
    """Parser for CSV files - converts rows to searchable documents."""

    def __init__(self, batch_size: int = 50, max_batches: int = 100):
        self.batch_size = batch_size
        self.max_batches = max_batches

    def parse(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parse CSV content into chunks.
        Groups rows into batches for efficient embedding.
        """
        chunks = []

        # Read CSV
        df = pd.read_csv(io.BytesIO(content))

        # Create summary chunk with column info and sample data
        summary = self._create_summary(df, filename)
        chunks.append(
            self._create_chunk(
                content=summary,
                filename=filename,
                chunk_type="summary",
                extra_metadata={"rows": len(df), "columns": list(df.columns)},
            )
        )

        # Create batched chunks (groups of rows as markdown tables)
        num_batches = min((len(df) + self.batch_size - 1) // self.batch_size, self.max_batches)

        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]

            batch_md = batch_df.to_markdown(index=False)
            chunks.append(
                self._create_chunk(
                    content=f"Tax records from {filename} (rows {start_idx+1}-{end_idx}):\n\n{batch_md}",
                    filename=filename,
                    chunk_type="table_batch",
                    extra_metadata={"start_row": start_idx, "end_row": end_idx},
                )
            )

        return chunks

    def _create_summary(self, df: pd.DataFrame, filename: str) -> str:
        """Create a summary of the CSV data."""
        summary_parts = [
            f"CSV Data Summary from {filename}:",
            f"Total records: {len(df)}",
            f"Columns: {', '.join(df.columns)}",
            "",
            "Sample data (first 5 rows):",
            df.head().to_markdown(index=False),
        ]

        # Add column statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append("")
            summary_parts.append("Numeric column statistics:")
            stats = df[numeric_cols].describe().round(2)
            summary_parts.append(stats.to_markdown())

        return "\n".join(summary_parts)
