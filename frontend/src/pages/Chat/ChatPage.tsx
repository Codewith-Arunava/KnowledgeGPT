import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { kbApi, chatApi, feedbackApi } from '@/api';
import type { KnowledgeBase, Conversation, Message, Citation, ChatResponse, LLMModel } from '@/types';
import { useChatStore } from '@/stores/chatStore';
import {
  Send, Loader2, MessageSquare, Trash2, Plus, Copy, Check,
  ThumbsUp, ThumbsDown, ChevronDown, Microscope, Globe,
  FileText, Shield, TrendingUp, Brain, X, Bot, User2
} from 'lucide-react';

const LLM_MODELS: { value: LLMModel; label: string; provider: string }[] = [
  { value: 'gpt-4o', label: 'GPT-4o', provider: 'OpenAI' },
  { value: 'gpt-4.1', label: 'GPT-4.1', provider: 'OpenAI' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini', provider: 'OpenAI' },
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro', provider: 'Google' },
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', provider: 'Google' },
];

const SEARCH_TYPES = [
  { value: 'similarity', label: 'Similarity' },
  { value: 'mmr', label: 'MMR (Diverse)' },
  { value: 'hybrid', label: 'Hybrid' },
];

// ─── Citation Panel ───────────────────────────────────────────────
function CitationPanel({ citations, onClose }: { citations: Citation[]; onClose: () => void }) {
  return (
    <div className="w-80 flex-shrink-0 border-l border-[hsl(var(--border)/0.5)] flex flex-col animate-slide-in">
      <div className="p-4 border-b border-[hsl(var(--border)/0.5)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText size={14} className="text-[hsl(var(--primary))]" />
          <h3 className="text-sm font-semibold text-[hsl(var(--text))]">Citations ({citations.length})</h3>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-[hsl(var(--surface-elevated))] text-[hsl(var(--text-muted))]">
          <X size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {citations.map((c, i) => (
          <div key={i} className="glass rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-5 h-5 rounded-full bg-[hsl(var(--primary)/0.2)] text-[hsl(var(--primary))] text-xs flex items-center justify-center font-bold flex-shrink-0">
                {i + 1}
              </span>
              <span className="text-xs font-medium text-[hsl(var(--text))] truncate">{c.document_name}</span>
            </div>
            <p className="text-xs text-[hsl(var(--text-muted))] mb-2">Page {c.page_number}</p>
            <p className="text-xs text-[hsl(var(--text))] bg-[hsl(var(--surface-elevated))] rounded-lg p-2 leading-relaxed">
              "{c.content_preview}..."
            </p>
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-1 bg-[hsl(var(--border))] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${c.similarity_score * 100}%`,
                    background: 'hsl(var(--primary))',
                  }}
                />
              </div>
              <span className="text-xs text-[hsl(var(--text-muted))]">{(c.similarity_score * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Agent Trace Panel ────────────────────────────────────────────
function AgentTracePanel({ trace }: { trace: NonNullable<ChatResponse['agent_trace']> }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs text-[hsl(var(--text-muted))] hover:text-[hsl(var(--primary))] transition-colors"
      >
        <Brain size={12} />
        <span>Agent trace</span>
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="mt-2 glass rounded-xl p-3 text-xs space-y-2 animate-fade-in">
          <div className="grid grid-cols-2 gap-2">
            {trace.query_intent && (
              <div><span className="text-[hsl(var(--text-muted))]">Intent: </span><span className="text-[hsl(var(--primary))] font-medium">{trace.query_intent}</span></div>
            )}
            {trace.chunks_retrieved !== undefined && (
              <div><span className="text-[hsl(var(--text-muted))]">Chunks: </span><span className="font-medium text-[hsl(var(--text))]">{trace.chunks_retrieved}</span></div>
            )}
            {trace.hallucination_risk && (
              <div><span className="text-[hsl(var(--text-muted))]">Hallucination: </span>
                <span className={`font-medium ${trace.hallucination_risk === 'low' ? 'text-[hsl(var(--success))]' : trace.hallucination_risk === 'medium' ? 'text-[hsl(var(--warning))]' : 'text-[hsl(var(--error))]'}`}>
                  {trace.hallucination_risk}
                </span>
              </div>
            )}
            {trace.answer_confidence !== undefined && (
              <div><span className="text-[hsl(var(--text-muted))]">Confidence: </span><span className="text-[hsl(var(--success))] font-medium">{(trace.answer_confidence * 100).toFixed(0)}%</span></div>
            )}
          </div>
          {trace.agents_executed && (
            <div>
              <span className="text-[hsl(var(--text-muted))]">Agents: </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {trace.agents_executed.map((a) => (
                  <span key={a} className="px-1.5 py-0.5 rounded bg-[hsl(var(--primary)/0.1)] text-[hsl(var(--primary))]">{a}</span>
                ))}
              </div>
            </div>
          )}
          {trace.web_search_used && (
            <div className="flex items-center gap-1 text-[hsl(var(--secondary))]">
              <Globe size={11} /> Web search was triggered
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Message Bubble ───────────────────────────────────────────────
function MessageBubble({ msg, onCitationsClick }: { msg: Message; onCitationsClick: (cits: Citation[]) => void }) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState<boolean | null>(null);
  const isUser = msg.role === 'user';

  const copy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const submitFeedback = async (type: 'like' | 'dislike') => {
    setLiked(type === 'like');
    try { await feedbackApi.submit({ message_id: msg.id, feedback_type: type }); } catch { /* best-effort */ }
  };

  return (
    <div className={`flex gap-3 animate-fade-in ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${isUser ? 'gradient-primary' : 'bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))]'}`}>
        {isUser ? <User2 size={14} className="text-white" /> : <Bot size={14} className="text-[hsl(var(--primary))]" />}
      </div>

      <div className={`flex-1 max-w-3xl ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* Bubble */}
        <div className={`rounded-2xl px-4 py-3 ${isUser ? 'gradient-primary text-white rounded-tr-none' : 'glass rounded-tl-none border border-[hsl(var(--border)/0.5)]'}`}>
          {isUser ? (
            <p className="text-sm leading-relaxed">{msg.content}</p>
          ) : (
            <div className="prose-dark text-sm leading-relaxed">
              <ReactMarkdown
                components={{
                  code({ className, children, ...props }: {
                    className?: string;
                    children?: React.ReactNode;
                    [key: string]: unknown;
                  }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const inline = !match;
                    return inline ? (
                      <code className={className} {...props}>{children}</code>
                    ) : (
                      <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div">
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    );
                  },
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Actions (assistant only) */}
        {!isUser && (
          <div className="flex items-center gap-3 mt-2 ml-1">
            <button onClick={copy} className="flex items-center gap-1 text-xs text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] transition-colors">
              {copied ? <Check size={12} className="text-[hsl(var(--success))]" /> : <Copy size={12} />}
              {copied ? 'Copied' : 'Copy'}
            </button>

            {msg.citations && msg.citations.length > 0 && (
              <button
                onClick={() => onCitationsClick(msg.citations as Citation[])}
                className="flex items-center gap-1 text-xs text-[hsl(var(--primary))] hover:text-[hsl(var(--primary))] transition-colors"
              >
                <FileText size={12} />{msg.citations.length} citation{msg.citations.length !== 1 ? 's' : ''}
              </button>
            )}

            {msg.retrieval_score !== undefined && msg.retrieval_score !== null && (
              <span className="flex items-center gap-1 text-xs text-[hsl(var(--text-muted))]">
                <TrendingUp size={11} />{(msg.retrieval_score * 100).toFixed(0)}% retrieved
              </span>
            )}

            {msg.hallucination_score !== undefined && msg.hallucination_score !== null && (
              <span className={`flex items-center gap-1 text-xs ${msg.hallucination_score < 0.3 ? 'text-[hsl(var(--success))]' : msg.hallucination_score < 0.7 ? 'text-[hsl(var(--warning))]' : 'text-[hsl(var(--error))]'}`}>
                <Shield size={11} />{msg.hallucination_score < 0.3 ? 'Low' : msg.hallucination_score < 0.7 ? 'Med' : 'High'} hallucination
              </span>
            )}

            <div className="flex items-center gap-1 ml-auto">
              <button
                onClick={() => submitFeedback('like')}
                className={`p-1 rounded-lg transition-all ${liked === true ? 'text-[hsl(var(--success))] bg-[hsl(var(--success)/0.1)]' : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--success))]'}`}
              >
                <ThumbsUp size={12} />
              </button>
              <button
                onClick={() => submitFeedback('dislike')}
                className={`p-1 rounded-lg transition-all ${liked === false ? 'text-[hsl(var(--error))] bg-[hsl(var(--error)/0.1)]' : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--error))]'}`}
              >
                <ThumbsDown size={12} />
              </button>
            </div>

            {msg.agent_trace && <AgentTracePanel trace={msg.agent_trace as Record<string, unknown>} />}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Typing Indicator ─────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-xl bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))] flex items-center justify-center">
        <Bot size={14} className="text-[hsl(var(--primary))]" />
      </div>
      <div className="glass rounded-2xl rounded-tl-none px-4 py-3 border border-[hsl(var(--border)/0.5)]">
        <div className="flex items-center gap-1 h-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--primary))] typing-dot" style={{ animationDelay: `${i * 160}ms` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main Chat Page ───────────────────────────────────────────────
export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { selectedModel, deepResearch, searchType, setModel, setDeepResearch, setSearchType } = useChatStore();

  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [activeConvId, setActiveConvId] = useState<string | undefined>(conversationId);
  const [activeCitations, setActiveCitations] = useState<Citation[] | null>(null);

  const { data: kbs = [] } = useQuery({
    queryKey: ['kbs'],
    queryFn: () => kbApi.list().then((r) => r.data as KnowledgeBase[]),
  });

  const { data: conversations = [] } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => chatApi.conversations().then((r) => r.data.conversations as Conversation[]),
  });

  // Load conversation on mount if conversationId provided
  useEffect(() => {
    if (conversationId) {
      chatApi.conversation(conversationId).then(({ data }) => {
        setMessages(data.messages || []);
        setActiveConvId(conversationId);
        const kb = kbs.find((k) => k.id === data.knowledge_base_id);
        if (kb) setSelectedKB(kb);
      }).catch(() => {});
    }
  }, [conversationId, kbs]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMutation = useMutation({
    mutationFn: (payload: object) => chatApi.send(payload),
    onSuccess: ({ data }: { data: ChatResponse }) => {
      qc.invalidateQueries({ queryKey: ['conversations'] });
      if (!activeConvId) {
        setActiveConvId(data.conversation_id);
        navigate(`/chat/${data.conversation_id}`, { replace: true });
      }
      const assistantMsg: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.answer,
        model_used: data.model_used,
        retrieval_score: data.retrieval_score ?? undefined,
        hallucination_score: data.hallucination_score ?? undefined,
        citation_confidence: data.agent_trace?.citation_confidence,
        answer_confidence: data.agent_trace?.answer_confidence,
        tokens_used: data.tokens_used ?? undefined,
        response_time_ms: data.response_time_ms ?? undefined,
        citations: data.citations,
        agent_trace: data.agent_trace ?? undefined,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || !selectedKB || sendMutation.isPending) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    const q = input.trim();
    setInput('');

    sendMutation.mutate({
      knowledge_base_id: selectedKB.id,
      message: q,
      conversation_id: activeConvId,
      model: selectedModel,
      deep_research: deepResearch,
      search_type: searchType,
      top_k: 5,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const newChat = () => {
    setMessages([]);
    setActiveConvId(undefined);
    navigate('/chat', { replace: true });
  };

  const deleteConv = async (id: string) => {
    await chatApi.deleteConversation(id);
    qc.invalidateQueries({ queryKey: ['conversations'] });
    if (id === activeConvId) newChat();
  };

  return (
    <div className="flex h-full">
      {/* ─── Conv Sidebar ─── */}
      <div className="w-64 flex-shrink-0 border-r border-[hsl(var(--border)/0.5)] flex flex-col">
        <div className="p-3 border-b border-[hsl(var(--border)/0.5)]">
          <button
            id="new-chat-btn"
            onClick={newChat}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl gradient-primary text-white text-sm font-medium hover:opacity-90 transition-all"
          >
            <Plus size={14} /><span>New Chat</span>
          </button>
        </div>

        {/* KB Selector */}
        <div className="p-3 border-b border-[hsl(var(--border)/0.5)]">
          <label className="text-xs text-[hsl(var(--text-muted))] mb-1.5 block">Knowledge Base</label>
          <select
            value={selectedKB?.id || ''}
            onChange={(e) => setSelectedKB(kbs.find((k) => k.id === e.target.value) || null)}
            className="w-full text-xs px-2 py-2 rounded-lg bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text))] focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
          >
            <option value="">Select knowledge base...</option>
            {kbs.map((kb) => <option key={kb.id} value={kb.id}>{kb.name}</option>)}
          </select>
        </div>

        {/* Conversations */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <p className="text-xs text-[hsl(var(--text-muted))] px-2 py-1">Recent</p>
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => { navigate(`/chat/${conv.id}`); }}
              className={`group flex items-center gap-2 px-3 py-2 rounded-xl cursor-pointer transition-all ${
                activeConvId === conv.id
                  ? 'bg-[hsl(var(--primary)/0.1)] border border-[hsl(var(--primary)/0.3)]'
                  : 'hover:bg-[hsl(var(--surface-elevated))]'
              }`}
            >
              <MessageSquare size={12} className="text-[hsl(var(--text-muted))] flex-shrink-0" />
              <span className="text-xs text-[hsl(var(--text))] truncate flex-1">{conv.title}</span>
              <button
                onClick={(e) => { e.stopPropagation(); deleteConv(conv.id); }}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-[hsl(var(--text-muted))] hover:text-[hsl(var(--error))] transition-all"
              >
                <Trash2 size={11} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ─── Chat Area ─── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="px-6 py-3 border-b border-[hsl(var(--border)/0.5)] flex items-center gap-3">
          <div className="flex-1 flex items-center gap-3">
            {/* Model selector */}
            <select
              value={selectedModel}
              onChange={(e) => setModel(e.target.value as LLMModel)}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text))] focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
            >
              {LLM_MODELS.map((m) => <option key={m.value} value={m.value}>{m.label} ({m.provider})</option>)}
            </select>

            {/* Search type */}
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as 'similarity' | 'mmr' | 'hybrid')}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text))] focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
            >
              {SEARCH_TYPES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>

          {/* Deep Research toggle */}
          <button
            id="deep-research-btn"
            onClick={() => setDeepResearch(!deepResearch)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              deepResearch
                ? 'bg-[hsl(var(--accent)/0.2)] text-[hsl(var(--accent))] border border-[hsl(var(--accent)/0.4)]'
                : 'bg-[hsl(var(--surface-elevated))] text-[hsl(var(--text-muted))] border border-[hsl(var(--border))] hover:border-[hsl(var(--accent)/0.4)]'
            }`}
          >
            <Microscope size={13} />
            Deep Research
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full space-y-4 animate-fade-in">
              <div className="w-20 h-20 rounded-3xl gradient-primary flex items-center justify-center shadow-2xl">
                <Brain size={36} className="text-white" />
              </div>
              <div className="text-center">
                <h2 className="text-xl font-bold text-[hsl(var(--text))] mb-2">
                  {selectedKB ? `Chat with "${selectedKB.name}"` : 'Select a Knowledge Base'}
                </h2>
                <p className="text-[hsl(var(--text-muted))] text-sm max-w-sm">
                  {selectedKB
                    ? 'Ask anything about your documents. I\'ll retrieve relevant context and generate a cited answer.'
                    : 'Choose a knowledge base from the sidebar to start chatting with your documents.'}
                </p>
              </div>
              {selectedKB && (
                <div className="grid grid-cols-2 gap-2 max-w-sm w-full">
                  {['Summarize the key findings', 'What are the main topics?', 'Explain the methodology', 'Compare the approaches'].map((q) => (
                    <button
                      key={q}
                      onClick={() => { setInput(q); inputRef.current?.focus(); }}
                      className="text-left p-3 rounded-xl glass hover:glass-elevated text-xs text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] transition-all border border-[hsl(var(--border)/0.5)]"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} onCitationsClick={setActiveCitations} />
            ))
          )}
          {sendMutation.isPending && <TypingIndicator />}
          {sendMutation.isError && (
            <div className="flex justify-center">
              <p className="text-xs text-[hsl(var(--error))] bg-[hsl(var(--error)/0.1)] px-3 py-1.5 rounded-xl">
                Failed to send. Check your API keys and try again.
              </p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-[hsl(var(--border)/0.5)]">
          {deepResearch && (
            <div className="mb-3 px-3 py-2 rounded-xl bg-[hsl(var(--accent)/0.1)] border border-[hsl(var(--accent)/0.3)] flex items-center gap-2">
              <Microscope size={13} className="text-[hsl(var(--accent))]" />
              <span className="text-xs text-[hsl(var(--accent))]">Deep Research mode — will generate comprehensive research report</span>
            </div>
          )}
          <div className="flex items-end gap-3 glass rounded-2xl p-3 border border-[hsl(var(--border)/0.5)] focus-within:border-[hsl(var(--primary)/0.5)] transition-all">
            <textarea
              ref={inputRef}
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={selectedKB ? `Ask about "${selectedKB.name}"...` : 'Select a knowledge base first...'}
              disabled={!selectedKB || sendMutation.isPending}
              rows={1}
              className="flex-1 bg-transparent text-[hsl(var(--text))] text-sm placeholder:text-[hsl(var(--text-muted))] focus:outline-none resize-none max-h-40 leading-relaxed"
              style={{ minHeight: '24px' }}
              onInput={(e) => {
                const t = e.currentTarget;
                t.style.height = 'auto';
                t.style.height = `${Math.min(t.scrollHeight, 160)}px`;
              }}
            />
            <button
              id="send-btn"
              onClick={handleSend}
              disabled={!input.trim() || !selectedKB || sendMutation.isPending}
              className="p-2.5 rounded-xl gradient-primary text-white disabled:opacity-40 hover:opacity-90 active:scale-95 transition-all flex-shrink-0"
            >
              {sendMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
          <p className="text-xs text-[hsl(var(--text-muted))] text-center mt-2">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* ─── Citation Panel ─── */}
      {activeCitations && (
        <CitationPanel citations={activeCitations} onClose={() => setActiveCitations(null)} />
      )}
    </div>
  );
}
