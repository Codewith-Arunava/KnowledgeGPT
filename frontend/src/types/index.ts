// ─── Auth ─────────────────────────────────────────────────────
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ─── Knowledge Base ───────────────────────────────────────────
export type VectorStoreType = 'chromadb' | 'pinecone';
export type RetrieverType = 'langchain' | 'llamaindex';
export type EmbeddingModel = 'openai-small' | 'openai-large' | 'gemini' | 'bge-large' | 'sentence-transformers';
export type LLMModel = 'gpt-4o' | 'gpt-4.1' | 'gpt-4o-mini' | 'gemini-2.5-pro' | 'gemini-2.5-flash';

export interface KnowledgeBase {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  vector_store: VectorStoreType;
  retriever_type: RetrieverType;
  embedding_model: EmbeddingModel;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string;
  vector_store: VectorStoreType;
  retriever_type: RetrieverType;
  embedding_model: EmbeddingModel;
}

// ─── Documents ────────────────────────────────────────────────
export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed';

export interface Document {
  id: string;
  knowledge_base_id: string;
  filename: string;
  original_filename: string;
  file_size: number | null;
  pages: number | null;
  chunks: number | null;
  status: DocumentStatus;
  error_message: string | null;
  uploaded_at: string;
  processed_at: string | null;
}

// ─── Chat ─────────────────────────────────────────────────────
export interface Citation {
  document_name: string;
  page_number: number;
  chunk_id: string;
  content_preview: string;
  similarity_score: number;
}

export interface AgentTrace {
  query_intent?: string;
  query_type?: string;
  entities?: string[];
  chunks_retrieved?: number;
  retrieval_scores?: number[];
  hallucination_risk?: string;
  hallucination_score?: number;
  citation_confidence?: number;
  answer_confidence?: number;
  research_notes?: string;
  web_search_used?: boolean;
  agents_executed?: string[];
}

export interface ChatRequest {
  knowledge_base_id: string;
  message: string;
  conversation_id?: string;
  model: LLMModel;
  deep_research: boolean;
  retriever_type?: RetrieverType;
  search_type: 'similarity' | 'mmr' | 'hybrid';
  top_k: number;
}

export interface ChatResponse {
  message_id: string;
  conversation_id: string;
  answer: string;
  citations: Citation[];
  agent_trace: AgentTrace | null;
  retrieval_score: number | null;
  hallucination_score: number | null;
  tokens_used: number | null;
  response_time_ms: number | null;
  model_used: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model_used?: string;
  retrieval_score?: number;
  hallucination_score?: number;
  citation_confidence?: number;
  answer_confidence?: number;
  tokens_used?: number;
  response_time_ms?: number;
  citations?: Citation[];
  agent_trace?: AgentTrace;
  timestamp: string;
}

export interface Conversation {
  id: string;
  knowledge_base_id: string;
  title: string;
  model: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

// ─── Analytics ────────────────────────────────────────────────
export interface DailyStats {
  date: string;
  queries: number;
  uploads: number;
  tokens_used: number;
  avg_response_time_ms: number;
}

export interface AnalyticsSummary {
  total_knowledge_bases: number;
  total_documents: number;
  total_conversations: number;
  total_queries: number;
  avg_retrieval_score: number;
  avg_hallucination_score: number;
  total_tokens_used: number;
  estimated_cost_usd: number;
  avg_response_time_ms: number;
  daily_stats: DailyStats[];
  top_documents: Record<string, unknown>[];
  model_usage: Record<string, number>;
}

// ─── Evaluation ───────────────────────────────────────────────
export interface EvaluationReport {
  context_precision: { relevant_chunks: number; total_retrieved: number; precision_pct: number };
  retrieval_accuracy_trend: { date: string; accuracy: number }[];
  hallucination_breakdown: { low: number; medium: number; high: number; avg_score: number };
  confidence_scores: { retrieval_confidence: number; citation_confidence: number; answer_confidence: number };
  total_evaluated_queries: number;
}
