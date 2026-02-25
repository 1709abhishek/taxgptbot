# TaxGPT Financial Chatbot

> **Hybrid RAG Chatbot** combining Vector Search + Knowledge Graph for accurate financial Q&A

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

[Demo Video](#demo-video) | [Evaluation Results](#evaluation-results) | [API Docs](#api-reference)

---

## Table of Contents

- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)
- [Evaluation Results](#evaluation-results)
- [API Reference](#api-reference)
- [Local Development](#local-development)
- [Challenges & Solutions](#challenges--solutions)
- [Production Considerations](#production-considerations)
- [Author](#author)

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/taxgpt-financial-chatbot.git
cd taxgpt-financial-chatbot

# 2. Set up environment variables
cp .env.example backend/.env
# Edit backend/.env with your API keys (ANTHROPIC_API_KEY, VOYAGE_API_KEY, OPENAI_API_KEY)

# 3. Run with Docker (recommended)
docker-compose up --build
```

The app will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## System Architecture

### High-Level Architecture

```mermaid
flowchart TD
    subgraph UI["User Interface Layer"]
        Frontend["React + Tailwind\nChat Interface"]
    end

    subgraph API["FastAPI Backend"]
        ChatAPI["POST /api/chat"]
        IngestAPI["POST /api/ingest"]
        HealthAPI["GET /health"]
    end

    subgraph Core["Core Processing"]
        subgraph Ingestion["Data Ingestion"]
            CSVParser["CSV Parser\npandas + dimensions"]
            PDFParser["PDF Parser\nPyMuPDF + tables"]
            PPTParser["PPT Parser\npython-pptx"]
            GraphBuilder["Graph Builder\nLLM extraction"]
        end

        subgraph Retrieval["Hybrid Retrieval"]
            VectorSearch["Vector Search\nSemantic similarity"]
            GraphSearch["Graph Traversal\nEntity relationships"]
            RRFusion["RRF Fusion\nRank combination"]
        end

        subgraph RAG["RAG Pipeline"]
            QueryAnalyze["Query Analyzer"]
            ContextBuild["Context Builder"]
            ResponseGen["Response Generator\nGPT-4o / Claude"]
        end
    end

    subgraph Storage["Data Storage"]
        ChromaDB[("ChromaDB\n100K+ vectors")]
        NetworkX[("NetworkX\n5K+ nodes")]
    end

    subgraph External["External Services"]
        VoyageAI["Voyage AI\nEmbeddings"]
        LLM["OpenAI / Anthropic\nLLM"]
    end

    Frontend --> ChatAPI
    Frontend --> IngestAPI

    ChatAPI --> Retrieval
    ChatAPI --> RAG
    IngestAPI --> Ingestion

    CSVParser --> ChromaDB
    CSVParser --> NetworkX
    PDFParser --> ChromaDB
    PDFParser --> GraphBuilder
    PPTParser --> ChromaDB
    GraphBuilder --> NetworkX

    VectorSearch --> ChromaDB
    GraphSearch --> NetworkX
    VectorSearch --> RRFusion
    GraphSearch --> RRFusion

    RRFusion --> ContextBuild
    ContextBuild --> ResponseGen

    QueryAnalyze --> VoyageAI
    ResponseGen --> LLM
```

### Data Flow Pipeline

```mermaid
flowchart LR
    subgraph Sources["Data Sources"]
        CSV["CSV\n5000 tax records"]
        PDF["PDF\nIRS Form 1040\nUSC Title 26"]
        PPT["PPT\nTax Presentations"]
    end

    subgraph Process["Processing"]
        Parse["Parse &\nChunk"]
        Embed["Voyage AI\nEmbeddings"]
        Extract["LLM Entity\nExtraction"]
    end

    subgraph Store["Storage"]
        Vectors[("Vector Store\n100K chunks")]
        Graph[("Knowledge Graph\n5K nodes\n25K edges")]
    end

    CSV --> Parse
    PDF --> Parse
    PPT --> Parse

    Parse --> Embed
    Parse --> Extract

    Embed --> Vectors
    Extract --> Graph
```

---

## How It Works

### Hybrid Retrieval: The Core Innovation

Most RAG systems use vector search alone. This system combines **semantic vector search** with **structured graph traversal** for superior accuracy on financial queries.

```mermaid
flowchart TD
    Query["User Query\n'What is adjusted gross income?'"]

    Query --> Analyze["Query Analyzer\nExtract intent + entities"]

    Analyze --> Split{"Parallel\nRetrieval"}

    Split --> VPath["Vector Path"]
    Split --> GPath["Graph Path"]

    subgraph Vector["Vector Search"]
        VEmbed["Embed query\nVoyage AI"]
        VSim["Similarity search\nTop-K = 10"]
        VDiv["Smart diversity\ninjection"]
        VEmbed --> VSim --> VDiv
    end

    subgraph GraphDB["Graph Traversal"]
        GExtract["Extract entities\n'AGI', 'income'"]
        GFind["Find nodes\ncase-insensitive"]
        GTraverse["Traverse edges\nFOR_PERIOD, HAS_METRIC"]
        GExtract --> GFind --> GTraverse
    end

    VPath --> Vector
    GPath --> GraphDB

    Vector --> Fusion["RRF Fusion\nReciprocal Rank\nk=60"]
    GraphDB --> Fusion

    Fusion --> Context["Final Context\nTop 5 chunks"]

    Context --> RAG["RAG Pipeline\nGPT-4o / Claude"]

    RAG --> Response["Response\n+ Sources\n+ Confidence\n+ Graph Path"]
```

### Why Hybrid Retrieval?

| Approach | Strength | Weakness |
|----------|----------|----------|
| **Vector Only** | Semantic understanding, natural language | No relationship awareness |
| **Graph Only** | Structured relationships, multi-hop | Limited to extracted entities |
| **Hybrid (Ours)** | Best of both worlds | Slightly more complex |

**Example Query**: "Compare Q3 revenue to Q3 last year"
- **Vector**: Finds chunks mentioning "revenue" and "Q3"
- **Graph**: Traverses `Revenue_Q3_2024 --[COMPARED_TO]--> Revenue_Q3_2023`
- **Combined**: Both semantic context AND explicit relationships

---

### Knowledge Graph Schema

```mermaid
flowchart LR
    subgraph Entities["Entity Types"]
        Company["Company\nIRS, Treasury"]
        Metric["Metric\nAGI, EIC"]
        Period["Period\n2023, Q3"]
        Form["Form\n1040, Schedule D"]
        Segment["Segment\nSingle, MFJ"]
    end

    Company -->|"HAS_METRIC"| Metric
    Metric -->|"FOR_PERIOD"| Period
    Form -->|"CONTAINS"| Metric
    Segment -->|"HAS_METRIC"| Metric
    Metric -->|"COMPARED_TO"| Metric
    Metric -->|"DETERMINES"| Metric
```

**Graph Statistics:**
- **5,031 nodes** (entities + transactions)
- **25,000 edges** (relationships)
- **7 relationship types** (FOR_PERIOD, HAS_METRIC, COMPARED_TO, etc.)

**Sample Edges:**
```
Earned Income Credit --[FOR_PERIOD]--> 2023
Single Filing Status --[HAS_METRIC]--> Tax Amount
Taxable Income --[DETERMINES]--> Tax Amount
Form 1040 --[CONTAINS]--> Schedule D
```

---

### CSV Processing Strategy

The CSV parser creates **dimension chunks** with Q&A format for optimal semantic matching:

```mermaid
flowchart TD
    CSV["CSV File\n5000 records"]

    CSV --> Summary["Summary Chunk\nOverview + stats"]
    CSV --> Dims["Dimension Chunks\nOne per category"]
    CSV --> Batches["Table Batches\n50 rows each"]

    subgraph DimChunks["Dimension Chunks (Q&A Format)"]
        TaxType["Taxpayer Type\n'What types are in the data?'"]
        State["State\n'What states are represented?'"]
        Income["Income Source\n'What income sources?'"]
        Deduct["Deduction Type\n'What deductions?'"]
        Year["Tax Year\n'What years covered?'"]
    end

    Dims --> DimChunks
```

**Why Q&A Format?**

The dimension chunks embed the **question** alongside the **answer**:
```
Question: What are the different taxpayer types in the tax data?
Answer: There are 5 different taxpayer types:
- Corporation: 1061 records (21.2%)
- Individual: 954 records (19.1%)
...
```

When a user asks "What taxpayer types are there?", the semantic similarity is much higher because the chunk literally contains similar phrasing. This is a form of **Hypothetical Document Embedding (HyDE)**.

---

## Design Decisions & Trade-offs

### Technology Choices

| Component | Choice | Why | Alternative | Trade-off |
|-----------|--------|-----|-------------|-----------|
| **Vector DB** | ChromaDB | Free, local, persistent, Railway-compatible | Pinecone | Pinecone needs paid tier |
| **Graph DB** | NetworkX | Zero setup, fast for <10K nodes | Neo4j | Neo4j overkill for demo |
| **Embeddings** | Voyage AI `voyage-finance-2` | Finance-specific, 1024 dims | OpenAI | OpenAI is generic |
| **LLM** | GPT-4o + Claude | Dual provider support | Single provider | More complexity |
| **Entity Extraction** | LLM-based | Handles financial jargon | Spacy NER | Spacy misses nuance |
| **Table Handling** | Markdown conversion | Preserves structure | Raw text | Raw loses context |
| **Frontend** | React + Tailwind | Professional, full-stack | Streamlit | Streamlit is common |

### Critical Design Decisions

#### 1. LLM-Based Entity Extraction (Not Spacy)

**Problem**: Financial documents contain nuanced metrics that Spacy NER misses.

```
Spacy:  "Adjusted EBITDA margin" → UNKNOWN
LLM:    "Adjusted EBITDA margin excluding restructuring" → METRIC
```

**Trade-off**: Slower ingestion (~2s per chunk) but dramatically better graph quality.

#### 2. Tables → Markdown Before Embedding

**Problem**: Standard chunking destroys table structure.

```
Bad:  "Revenue 56.2B Q3 2024 52.1B Q3 2023"
Good: "| Metric | Q3 2024 | Q3 2023 |\n|---|---|---|\n| Revenue | 56.2B | 52.1B |"
```

The embedding model can now understand row/column relationships.

#### 3. Smart Source Diversity Injection

**Problem**: 100K PDF chunks drown out 105 CSV chunks in retrieval.

```python
# Don't force diversity - inject only when relevant
if minority_result.score >= 0.65 and source not in top_results:
    inject(minority_result)
```

**Trade-off**: Slightly more complex ranking logic, but prevents source domination.

#### 4. Dual LLM Provider Support

**Problem**: Anthropic API returned `529 Overloaded` during evaluation.

**Solution**: Added OpenAI GPT-4o as fallback with easy switching via `.env`:

```bash
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4o     # or claude-sonnet-4-20250514
```

#### 5. Background Processing for Large PDFs

**Problem**: 7700-page PDFs cause HTTP timeouts.

```mermaid
flowchart LR
    Upload["POST /api/ingest/async"]
    BG["Background Task"]
    Progress["GET /status/{id}"]
    Complete["Completion"]

    Upload -->|"Returns immediately"| BG
    BG -->|"Poll"| Progress
    Progress -->|"Done"| Complete
```

**Trade-off**: Lost if server restarts, but sufficient for demo. Would use Celery + Redis in production.

---

## Evaluation Results

### Current Metrics (41 Questions)

| Metric | Score |
|--------|-------|
| **Recall@5** | **80.49%** (33/41) |
| **MRR@5** | **0.671** |
| **Avg Confidence** | ~0.80 |

### Store Statistics

| Store | Count |
|-------|-------|
| Vector chunks | 100,280 |
| Graph nodes | 5,031 |
| Graph edges | 25,000 |

### Results by Source Type

| Source | Questions | Found | Rate |
|--------|-----------|-------|------|
| tax_data_taxgpt.csv | 7 | 5 | 71% |
| i1040gi_taxgpt.pdf | 23 | 19 | 83% |
| usc26@118-78_taxgpt.pdf | 7 | 7 | **100%** |
| MIC_3e_Ch11_taxgpt.ppt | 4 | 4 | **100%** |

### Improvement History

```mermaid
flowchart LR
    A["Initial\n68.42%"]
    B["OpenAI\nIntegration"]
    C["RAG Tuning\n73.68%"]
    D["CSV Dims\n78.95%"]
    E["Final\n80.49%"]

    A --> B --> C --> D --> E

    style E fill:#90EE90
```

### Sample Working Questions

**CSV:**
- "What are the different taxpayer types?" ✓
- "What tax years are covered?" ✓

**PDF:**
- "What is adjusted gross income?" ✓
- "What are Form 1040 Helpful Hints?" ✓
- "What happens if you fraudulently claim EIC?" ✓

**PPT:**
- "How does demand elasticity affect tax burden?" ✓
- "How does US compare to other countries in tax receipts?" ✓

### Known Limitations

| Issue | Cause | Fix |
|-------|-------|-----|
| CSV aggregation queries | RAG doesn't compute averages | Add SQL layer |
| Some PDF source confusion | Similar content in multiple docs | Better filtering |

**Run evaluation yourself:**
```bash
cd backend && python scripts/evaluate.py
```

---

## API Reference

### Chat Endpoint

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "What is adjusted gross income?",
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "answer": "Adjusted Gross Income (AGI) is your total gross income minus specific deductions...",
  "confidence": 0.85,
  "sources": [
    {
      "file": "i1040gi_taxgpt.pdf",
      "page": 12,
      "snippet": "Your adjusted gross income (AGI) is...",
      "score": 0.87
    }
  ],
  "graph_path": [
    {"node": "Adjusted Gross Income", "type": "metric"},
    {"edge": "DETERMINES"},
    {"node": "Taxable Income", "type": "metric"}
  ]
}
```

### Ingestion Endpoints

```bash
# Synchronous (small files)
POST /api/ingest
Content-Type: multipart/form-data
file: document.pdf

# Asynchronous (large files)
POST /api/ingest/async
Content-Type: multipart/form-data
file: large_document.pdf

# Check progress
GET /api/ingest/status/{task_id}

# List all tasks
GET /api/ingest/tasks
```

### Health Check

```bash
GET /health

{
  "status": "healthy",
  "vector_store": {"document_count": 100280},
  "graph_store": {"node_count": 5031, "edge_count": 25000}
}
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- LibreOffice (for old .ppt format support): `brew install --cask libreoffice`

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

### Environment Variables

```bash
# Required API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
VOYAGE_API_KEY=pa-...

# LLM Configuration
LLM_PROVIDER=openai          # or anthropic
LLM_MODEL=gpt-4o             # or claude-sonnet-4-20250514

# Embedding Configuration
EMBEDDING_PROVIDER=voyage
EMBEDDING_MODEL=voyage-finance-2

# Storage
CHROMA_PERSIST_DIR=./data/chroma_db
GRAPH_PERSIST_PATH=./data/graph.pkl

# Performance (for 8GB machines)
LOW_MEMORY_MODE=true
LOW_MEMORY_MAX_WORKERS=2
LOW_MEMORY_EMBEDDING_BATCH_SIZE=8
```

### Running Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run evaluation
python scripts/evaluate.py
```

---

## Challenges & Solutions

### Bug Fixes Applied

#### 1. Confidence Score Always 2%

**Problem**: ChromaDB cosine distance ranges 0-2, not 0-1.

```python
# Before (wrong)
score = 1 - distance  # Could be negative!

# After (fixed)
score = max(0, 1 - (distance / 2))  # Properly normalized
```

#### 2. PPT Content Never Retrieved

**Problem**: 3 PPT chunks among 100K+ vectors got drowned out.

**Solution**: Changed from 3 large chunks to 11 overlapping windows (4 slides per window, step=2).

#### 3. CSV Data Not Retrievable

**Problem**: Questions about CSV returned PDF results.

**Solution**: Added Q&A dimension chunks + smart diversity injection.

#### 4. Graph Entity Extraction Failing

**Problem**: `KeyError: '\n  "entities"'` due to JSON curly braces in prompt.

**Solution**: Escaped curly braces: `{{` and `}}`

#### 5. Old .ppt Format Support

**Problem**: Files with `.pptx` extension but old binary format failed.

**Solution**: Detect by magic bytes, not extension:
```python
is_ole = content[:4] == b'\xD0\xCF\x11\xE0'
```

#### 6. Graph Case-Sensitivity Bug

**Problem**: LLM extracted `'adjusted gross income'`, graph stored `'Adjusted Gross Income'`.

**Solution**: Case-insensitive node matching.

#### 7. Forced Diversity Breaking PDF Queries

**Problem**: After fixing CSV retrieval, PDF queries returned wrong results.

**Solution**: Smart injection only when score >= 0.65 AND not already present.

---

## Production Considerations

### What I Would Change

```mermaid
flowchart TD
    subgraph Current["Current (Demo)"]
        C1["NetworkX\nIn-Memory"]
        C2["ChromaDB\nLocal"]
        C3["BackgroundTasks\nVolatile"]
        C4["No Auth"]
    end

    subgraph Prod["Production"]
        P1["Neo4j Aura\nDistributed"]
        P2["Pinecone\nManaged"]
        P3["Celery + Redis\nPersistent"]
        P4["JWT/OAuth2"]
    end

    C1 -.->|"Scale"| P1
    C2 -.->|"Scale"| P2
    C3 -.->|"Reliability"| P3
    C4 -.->|"Security"| P4
```

| Component | Current | Production |
|-----------|---------|------------|
| Graph DB | NetworkX | Neo4j Aura |
| Vector DB | ChromaDB | Pinecone / Weaviate |
| Task Queue | BackgroundTasks | Celery + Redis |
| Caching | None | Redis |
| Auth | None | JWT / OAuth2 |
| Monitoring | Logs | Datadog / Prometheus |

### Cost Estimate (1 Week Testing)

| Service | Usage | Cost |
|---------|-------|------|
| Railway hosting | Backend + Frontend | ~$2.58 (free tier) |
| GPT-4o API | 350 queries | ~$3.00 |
| Voyage AI | Embeddings | ~$0.01 |
| **Total** | | **~$5.59** |

---

## Project Structure

```
taxgpt-financial-chatbot/
├── README.md
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py            # Settings
│   │   │
│   │   ├── ingestion/           # Data processing
│   │   │   ├── csv_parser.py    # Q&A dimension chunks
│   │   │   ├── pdf_parser.py    # Table→Markdown
│   │   │   ├── ppt_parser.py    # Overlapping windows
│   │   │   └── graph_builder.py # LLM extraction
│   │   │
│   │   ├── retrieval/           # Hybrid retrieval
│   │   │   ├── vector_store.py  # ChromaDB
│   │   │   ├── graph_store.py   # NetworkX
│   │   │   ├── hybrid.py        # RRF fusion
│   │   │   └── embeddings.py    # Voyage AI
│   │   │
│   │   ├── llm/                 # LLM orchestration
│   │   │   ├── client.py        # OpenAI/Anthropic
│   │   │   ├── prompts.py       # System prompts
│   │   │   └── rag_pipeline.py  # RAG flow
│   │   │
│   │   └── api/routes/          # Endpoints
│   │
│   ├── tests/
│   │   └── eval_dataset.json    # 41 Q&A pairs
│   │
│   └── scripts/
│       └── evaluate.py
│
└── frontend/
    └── src/
        ├── App.tsx
        └── components/
```

---

## Demo Video

[Watch the 3-5 minute demo](#) showing:

1. **Simple Query** (30s): "What is adjusted gross income?" → PDF answer with citation
2. **CSV Query** (30s): "What taxpayer types?" → Dimension chunk retrieval
3. **Graph Query** (60s): "How does demand elasticity affect tax burden?" → PPT + graph traversal
4. **Edge Case** (30s): Ambiguous query with confidence score
5. **File Upload** (30s): Ingesting new document with progress

---

## What Makes This Solution Stand Out

### 1. True Hybrid Retrieval
- Vector search + Graph traversal
- RRF fusion for ranking
- Most solutions use vector-only

### 2. Multi-Modal Data Understanding
- CSV: Q&A dimension chunks (HyDE-style)
- PDF: Table → Markdown preservation
- PPT: Overlapping window chunks

### 3. Production-Ready Architecture
- Dual LLM provider support
- Background task processing
- Comprehensive error handling
- Docker deployment ready

### 4. Documented Trade-offs
Every design decision includes:
- What we chose and why
- Alternatives considered
- Production migration path

### 5. Quantified Accuracy
- 41-question evaluation dataset
- 80.49% Recall@5
- Breakdown by source type
- Improvement history tracked

---

## Author

**Abhishek Jain**

- LinkedIn: [linkedin.com/in/abhishekjain](https://linkedin.com/in/abhishekjain)
- GitHub: [github.com/abhishekjain](https://github.com/abhishekjain)

---

*Built for TaxGPT Backend Engineering Assignment - February 2026*
