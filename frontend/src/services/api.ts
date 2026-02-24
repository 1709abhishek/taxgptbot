import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

export interface Source {
  file: string
  page?: number
  snippet: string
  chunk_id: string
}

export interface GraphNode {
  node: string
  type: string
  value?: string
}

export interface GraphEdge {
  edge: string
  direction: string
}

export interface RetrievalDebug {
  vector_results: number
  graph_results: number
  rrf_fused: number
}

export interface ChatResponse {
  answer: string
  confidence: number
  sources: Source[]
  graph_path: (GraphNode | GraphEdge)[]
  retrieval_debug: RetrievalDebug
  conversation_id: string
}

export interface IngestResponse {
  status: string
  documents_processed: number
  chunks_created: number
  entities_extracted: number
  graph_edges_created: number
  processing_time_seconds: number
}

export interface HealthResponse {
  status: string
  vector_count: number
  graph_nodes: number
  graph_edges: number
  last_ingestion?: string
}

export const api = {
  async chat(message: string, conversationId?: string): Promise<ChatResponse> {
    const response = await axios.post(`${API_BASE}/api/chat`, {
      message,
      conversation_id: conversationId,
    })
    return response.data
  },

  async ingest(files: File[]): Promise<IngestResponse> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    const response = await axios.post(`${API_BASE}/api/ingest`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async health(): Promise<HealthResponse> {
    const response = await axios.get(`${API_BASE}/health`)
    return response.data
  },
}
