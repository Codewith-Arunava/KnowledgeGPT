import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { kbApi, documentsApi } from '@/api';
import type { KnowledgeBase, Document, KnowledgeBaseCreate } from '@/types';
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import type { AxiosError } from 'axios';
import {
  Plus, Database, FileText, Trash2, Upload, ChevronRight,
  Loader2, CheckCircle, XCircle, Clock, RefreshCw, BookOpen, X
} from 'lucide-react';

const EMBEDDING_OPTIONS = [
  { value: 'openai-small', label: 'OpenAI text-embedding-3-small' },
  { value: 'openai-large', label: 'OpenAI text-embedding-3-large' },
  { value: 'gemini', label: 'Google Gemini Embeddings' },
  { value: 'bge-large', label: 'BGE Large (Local)' },
  { value: 'sentence-transformers', label: 'Sentence Transformers (Local)' },
];

const RETRIEVER_OPTIONS = [
  { value: 'langchain', label: 'LangChain Retriever' },
  { value: 'llamaindex', label: 'LlamaIndex Retriever' },
];

const VECTOR_STORE_OPTIONS = [
  { value: 'chromadb', label: 'ChromaDB (Local)' },
  { value: 'pinecone', label: 'Pinecone (Cloud)' },
];

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    ready: { color: 'text-[hsl(var(--success))] bg-[hsl(var(--success)/0.1)]', icon: <CheckCircle size={11} />, label: 'Ready' },
    processing: { color: 'text-[hsl(var(--warning))] bg-[hsl(var(--warning)/0.1)]', icon: <RefreshCw size={11} className="animate-spin" />, label: 'Processing' },
    pending: { color: 'text-[hsl(var(--text-muted))] bg-[hsl(var(--border)/0.5)]', icon: <Clock size={11} />, label: 'Pending' },
    failed: { color: 'text-[hsl(var(--error))] bg-[hsl(var(--error)/0.1)]', icon: <XCircle size={11} />, label: 'Failed' },
  };
  const s = map[status] || map.pending;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>
      {s.icon}{s.label}
    </span>
  );
}

function CreateKBModal({ onClose, onCreated }: { onClose: () => void; onCreated: (kb: KnowledgeBase) => void }) {
  const [form, setForm] = useState<KnowledgeBaseCreate>({
    name: '', description: '', vector_store: 'chromadb', retriever_type: 'langchain', embedding_model: 'openai-small',
  });
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => kbApi.create(form),
    onSuccess: ({ data }) => { qc.invalidateQueries({ queryKey: ['kbs'] }); onCreated(data); onClose(); },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="glass-elevated rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-[hsl(var(--text))]">Create Knowledge Base</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[hsl(var(--border)/0.5)] transition-all">
            <X size={16} className="text-[hsl(var(--text-muted))]" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide mb-1.5 block">Name *</label>
            <input
              value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Research Papers 2024"
              className="w-full px-3 py-2.5 rounded-xl bg-[hsl(var(--surface))] border border-[hsl(var(--border))] text-[hsl(var(--text))] text-sm focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide mb-1.5 block">Description</label>
            <textarea
              value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="What is this knowledge base for?"
              rows={2}
              className="w-full px-3 py-2.5 rounded-xl bg-[hsl(var(--surface))] border border-[hsl(var(--border))] text-[hsl(var(--text))] text-sm focus:outline-none focus:border-[hsl(var(--primary))] transition-all resize-none"
            />
          </div>
          {[
            { label: 'Embedding Model', field: 'embedding_model', options: EMBEDDING_OPTIONS },
            { label: 'Vector Store', field: 'vector_store', options: VECTOR_STORE_OPTIONS },
            { label: 'Retriever Engine', field: 'retriever_type', options: RETRIEVER_OPTIONS },
          ].map(({ label, field, options }) => (
            <div key={field}>
              <label className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide mb-1.5 block">{label}</label>
              <select
                value={form[field as keyof KnowledgeBaseCreate] as string}
                onChange={(e) => setForm({ ...form, [field]: e.target.value } as KnowledgeBaseCreate)}
                className="w-full px-3 py-2.5 rounded-xl bg-[hsl(var(--surface))] border border-[hsl(var(--border))] text-[hsl(var(--text))] text-sm focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
              >
                {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          ))}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-[hsl(var(--border))] text-[hsl(var(--text-muted))] text-sm hover:bg-[hsl(var(--surface-elevated))] transition-all">Cancel</button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.name || mutation.isPending}
            className="flex-1 py-2.5 rounded-xl gradient-primary text-white text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50 hover:opacity-90 transition-all"
          >
            {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}

function UploadZone({ kbId, onDone }: { kbId: string; onDone: () => void }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const onDrop = useCallback(async (files: File[]) => {
    setUploading(true); setError('');
    try {
      await documentsApi.upload(kbId, files);
      onDone();
    } catch (e) {
      const err = e as AxiosError<{ detail: string }>;
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [kbId, onDone]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf': ['.pdf'] }, multiple: true,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-[hsl(var(--primary))] bg-[hsl(var(--primary)/0.05)]'
            : 'border-[hsl(var(--border))] hover:border-[hsl(var(--primary)/0.5)] hover:bg-[hsl(var(--surface-elevated))]'
        }`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="flex flex-col items-center gap-2">
            <Loader2 size={24} className="animate-spin text-[hsl(var(--primary))]" />
            <p className="text-sm text-[hsl(var(--text-muted))]">Uploading & processing...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Upload size={24} className="text-[hsl(var(--text-muted))]" />
            <p className="text-sm font-medium text-[hsl(var(--text))]">
              {isDragActive ? 'Drop PDFs here' : 'Drag & drop PDFs or click to browse'}
            </p>
            <p className="text-xs text-[hsl(var(--text-muted))]">PDF only • Max 50MB per file</p>
          </div>
        )}
      </div>
      {error && <p className="mt-2 text-xs text-[hsl(var(--error))]">{error}</p>}
    </div>
  );
}

export default function KnowledgeBasePage() {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);

  const { data: kbs = [], isLoading } = useQuery({
    queryKey: ['kbs'],
    queryFn: () => kbApi.list().then((r) => r.data as KnowledgeBase[]),
  });

  const { data: docs = [], refetch: refetchDocs } = useQuery({
    queryKey: ['documents', selectedKB?.id],
    queryFn: () => selectedKB ? documentsApi.list(selectedKB.id).then((r) => r.data.documents as Document[]) : Promise.resolve([]),
    enabled: !!selectedKB,
    refetchInterval: 5000, // Poll for status updates
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => kbApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['kbs'] }); if (selectedKB) setSelectedKB(null); },
  });

  const deleteDocMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => refetchDocs(),
  });

  return (
    <div className="flex h-full animate-fade-in">
      {/* Left panel — KB list */}
      <div className="w-80 flex-shrink-0 border-r border-[hsl(var(--border)/0.5)] flex flex-col">
        <div className="p-4 border-b border-[hsl(var(--border)/0.5)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database size={16} className="text-[hsl(var(--primary))]" />
            <h2 className="font-semibold text-[hsl(var(--text))] text-sm">Knowledge Bases</h2>
          </div>
          <button
            id="create-kb-btn"
            onClick={() => setShowCreate(true)}
            className="p-1.5 rounded-lg gradient-primary text-white hover:opacity-90 transition-all"
          >
            <Plus size={14} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {isLoading ? (
            [...Array(4)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)
          ) : kbs.length === 0 ? (
            <div className="flex flex-col items-center gap-2 p-6 text-center">
              <BookOpen size={32} className="text-[hsl(var(--text-muted))]" />
              <p className="text-sm text-[hsl(var(--text-muted))]">No knowledge bases yet</p>
              <button onClick={() => setShowCreate(true)} className="text-xs text-[hsl(var(--primary))] hover:underline">Create one</button>
            </div>
          ) : (
            kbs.map((kb) => (
              <div
                key={kb.id}
                onClick={() => setSelectedKB(kb)}
                className={`p-3 rounded-xl cursor-pointer transition-all group ${
                  selectedKB?.id === kb.id
                    ? 'bg-[hsl(var(--primary)/0.1)] border border-[hsl(var(--primary)/0.3)]'
                    : 'hover:bg-[hsl(var(--surface-elevated))]'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[hsl(var(--text))] truncate">{kb.name}</p>
                    <p className="text-xs text-[hsl(var(--text-muted))] mt-0.5">{kb.document_count} docs • {kb.embedding_model}</p>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => { e.stopPropagation(); if (confirm('Delete this knowledge base?')) deleteMutation.mutate(kb.id); }}
                      className="p-1 rounded-lg hover:bg-[hsl(var(--error)/0.1)] hover:text-[hsl(var(--error))] text-[hsl(var(--text-muted))] transition-all"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-[hsl(var(--surface-elevated))] text-[hsl(var(--text-muted))]">{kb.vector_store}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-[hsl(var(--surface-elevated))] text-[hsl(var(--text-muted))]">{kb.retriever_type}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right panel — Document management */}
      <div className="flex-1 flex flex-col">
        {selectedKB ? (
          <>
            <div className="p-6 border-b border-[hsl(var(--border)/0.5)]">
              <div className="flex items-center gap-2 mb-1">
                <ChevronRight size={14} className="text-[hsl(var(--text-muted))]" />
                <h2 className="text-lg font-semibold text-[hsl(var(--text))]">{selectedKB.name}</h2>
              </div>
              {selectedKB.description && (
                <p className="text-sm text-[hsl(var(--text-muted))] mb-4">{selectedKB.description}</p>
              )}
              <UploadZone kbId={selectedKB.id} onDone={() => refetchDocs()} />
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileText size={15} className="text-[hsl(var(--text-muted))]" />
                <h3 className="text-sm font-semibold text-[hsl(var(--text))]">Documents ({docs.length})</h3>
              </div>
              <div className="space-y-2">
                {docs.map((doc) => (
                  <div key={doc.id} className="glass rounded-xl p-4 flex items-center gap-4 hover:glass-elevated transition-all animate-fade-in">
                    <div className="w-9 h-9 rounded-lg bg-[hsl(var(--error)/0.1)] flex items-center justify-center flex-shrink-0">
                      <FileText size={16} className="text-[hsl(var(--error))]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[hsl(var(--text))] truncate">{doc.original_filename}</p>
                      <p className="text-xs text-[hsl(var(--text-muted))] mt-0.5">
                        {doc.pages ? `${doc.pages} pages` : '—'} • {doc.chunks ? `${doc.chunks} chunks` : '—'} •{' '}
                        {doc.file_size ? `${(doc.file_size / 1024 / 1024).toFixed(1)}MB` : '—'}
                      </p>
                    </div>
                    <StatusBadge status={doc.status} />
                    <button
                      onClick={() => { if (confirm('Delete this document?')) deleteDocMutation.mutate(doc.id); }}
                      className="p-1.5 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--error))] hover:bg-[hsl(var(--error)/0.1)] transition-all"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
                {docs.length === 0 && (
                  <div className="text-center py-10 text-[hsl(var(--text-muted))] text-sm">
                    No documents uploaded yet. Upload PDFs above.
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <div className="w-16 h-16 rounded-2xl glass mx-auto flex items-center justify-center">
                <Database size={24} className="text-[hsl(var(--text-muted))]" />
              </div>
              <p className="text-[hsl(var(--text-muted))] text-sm">Select a knowledge base to manage documents</p>
            </div>
          </div>
        )}
      </div>

      {showCreate && <CreateKBModal onClose={() => setShowCreate(false)} onCreated={() => {}} />}
    </div>
  );
}
