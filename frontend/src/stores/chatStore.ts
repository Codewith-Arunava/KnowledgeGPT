import { create } from 'zustand';
import type { Conversation, Message, LLMModel } from '@/types';

interface ChatState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  selectedModel: LLMModel;
  deepResearch: boolean;
  searchType: 'similarity' | 'mmr' | 'hybrid';

  setConversations: (convs: Conversation[]) => void;
  setActiveConversation: (conv: Conversation | null) => void;
  addMessage: (msg: Message) => void;
  setMessages: (msgs: Message[]) => void;
  setLoading: (loading: boolean) => void;
  setModel: (model: LLMModel) => void;
  setDeepResearch: (dr: boolean) => void;
  setSearchType: (type: 'similarity' | 'mmr' | 'hybrid') => void;
  addConversation: (conv: Conversation) => void;
  removeConversation: (id: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  activeConversation: null,
  messages: [],
  isLoading: false,
  selectedModel: 'gpt-4o',
  deepResearch: false,
  searchType: 'similarity',

  setConversations: (conversations) => set({ conversations }),
  setActiveConversation: (conv) => set({ activeConversation: conv }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setMessages: (messages) => set({ messages }),
  setLoading: (isLoading) => set({ isLoading }),
  setModel: (selectedModel) => set({ selectedModel }),
  setDeepResearch: (deepResearch) => set({ deepResearch }),
  setSearchType: (searchType) => set({ searchType }),
  addConversation: (conv) => set((s) => ({ conversations: [conv, ...s.conversations] })),
  removeConversation: (id) =>
    set((s) => ({ conversations: s.conversations.filter((c) => c.id !== id) })),
}));
