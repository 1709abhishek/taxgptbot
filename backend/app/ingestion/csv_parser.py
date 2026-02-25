import io
from typing import List, Dict, Any
import pandas as pd

from .base import BaseParser


class CSVParser(BaseParser):
    """Parser for CSV files - converts rows to searchable documents."""

    # Expected column names for tax data CSV
    COLUMN_MAPPING = {
        "taxpayer_type": "Taxpayer Type",
        "tax_year": "Tax Year",
        "transaction_date": "Transaction Date",
        "income_source": "Income Source",
        "deduction_type": "Deduction Type",
        "state": "State",
        "income": "Income",
        "deductions": "Deductions",
        "taxable_income": "Taxable Income",
        "tax_rate": "Tax Rate",
        "tax_owed": "Tax Owed",
    }

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

    def build_graph_extractions(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Build structured graph extractions from CSV rows.

        Creates a star schema with Transaction nodes at the center,
        connected to dimension nodes (TaxpayerType, State, IncomeSource,
        DeductionType, TaxYear).

        Returns:
            List of extraction dicts compatible with GraphStore.add_extraction()
        """
        df = pd.read_csv(io.BytesIO(content))
        extractions = []

        # Check if this is a tax data CSV with expected columns
        required_cols = ["Taxpayer Type", "State", "Income Source", "Deduction Type", "Tax Year"]
        if not all(col in df.columns for col in required_cols):
            # Not a tax data CSV, skip graph building
            return []

        for idx, row in df.iterrows():
            # Create unique transaction ID
            tx_id = f"TX_{filename}_{idx}"

            # Extract values with safe defaults
            taxpayer_type = str(row.get("Taxpayer Type", "Unknown"))
            state = str(row.get("State", "Unknown"))
            income_source = str(row.get("Income Source", "Unknown"))
            deduction_type = str(row.get("Deduction Type", "Unknown"))
            tax_year = str(int(row.get("Tax Year", 0)))

            # Numeric values
            income = float(row.get("Income", 0))
            deductions = float(row.get("Deductions", 0))
            taxable_income = float(row.get("Taxable Income", 0))
            tax_rate = float(row.get("Tax Rate", 0))
            tax_owed = float(row.get("Tax Owed", 0))
            transaction_date = str(row.get("Transaction Date", ""))

            extraction = {
                "source_chunk_id": f"{filename}_row_{idx}",
                "source_file": filename,
                "entities": [
                    # Dimension nodes (will deduplicate in graph store)
                    {"type": "taxpayer_type", "name": taxpayer_type},
                    {"type": "state", "name": state},
                    {"type": "income_source", "name": income_source},
                    {"type": "deduction_type", "name": deduction_type},
                    {"type": "tax_year", "name": tax_year},
                    # Fact node with all numeric properties
                    {
                        "type": "transaction",
                        "name": tx_id,
                        "income": income,
                        "deductions": deductions,
                        "taxable_income": taxable_income,
                        "tax_rate": tax_rate,
                        "tax_owed": tax_owed,
                        "date": transaction_date,
                    },
                ],
                "relationships": [
                    {"from": tx_id, "to": taxpayer_type, "relation": "FILED_BY"},
                    {"from": tx_id, "to": state, "relation": "FILED_IN"},
                    {"from": tx_id, "to": income_source, "relation": "HAS_INCOME"},
                    {"from": tx_id, "to": deduction_type, "relation": "CLAIMED_DEDUCTION"},
                    {"from": tx_id, "to": tax_year, "relation": "FOR_YEAR"},
                ],
            }
            extractions.append(extraction)

        return extractions

    def get_graph_stats(self, content: bytes) -> Dict[str, Any]:
        """
        Get statistics about what the graph would contain.
        Useful for debugging and progress tracking.
        """
        df = pd.read_csv(io.BytesIO(content))

        stats = {
            "total_transactions": len(df),
            "unique_taxpayer_types": df["Taxpayer Type"].nunique() if "Taxpayer Type" in df.columns else 0,
            "unique_states": df["State"].nunique() if "State" in df.columns else 0,
            "unique_income_sources": df["Income Source"].nunique() if "Income Source" in df.columns else 0,
            "unique_deduction_types": df["Deduction Type"].nunique() if "Deduction Type" in df.columns else 0,
            "unique_tax_years": df["Tax Year"].nunique() if "Tax Year" in df.columns else 0,
            "total_nodes_estimate": len(df) + df["Taxpayer Type"].nunique() + df["State"].nunique() +
                                   df["Income Source"].nunique() + df["Deduction Type"].nunique() +
                                   df["Tax Year"].nunique() if all(col in df.columns for col in ["Taxpayer Type", "State", "Income Source", "Deduction Type", "Tax Year"]) else 0,
            "total_edges_estimate": len(df) * 5,  # 5 relationships per transaction
        }

        return stats
