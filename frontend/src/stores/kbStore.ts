import { create } from 'zustand';
import type { KnowledgeBase } from '@/types';

interface KBState {
  knowledgeBases: KnowledgeBase[];
  selectedKB: KnowledgeBase | null;
  setKnowledgeBases: (kbs: KnowledgeBase[]) => void;
  setSelectedKB: (kb: KnowledgeBase | null) => void;
  addKB: (kb: KnowledgeBase) => void;
  removeKB: (id: string) => void;
  updateKB: (kb: KnowledgeBase) => void;
}

export const useKBStore = create<KBState>((set) => ({
  knowledgeBases: [],
  selectedKB: null,

  setKnowledgeBases: (kbs) => set({ knowledgeBases: kbs }),
  setSelectedKB: (kb) => set({ selectedKB: kb }),
  addKB: (kb) => set((s) => ({ knowledgeBases: [kb, ...s.knowledgeBases] })),
  removeKB: (id) => set((s) => ({ knowledgeBases: s.knowledgeBases.filter((k) => k.id !== id) })),
  updateKB: (kb) =>
    set((s) => ({
      knowledgeBases: s.knowledgeBases.map((k) => (k.id === kb.id ? kb : k)),
    })),
}));
