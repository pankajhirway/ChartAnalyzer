import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  Annotation,
  AnnotationCreate,
  AnnotationUpdate,
  AnnotationListResponse,
  AnalysisNote,
  AnalysisNoteCreate,
  AnalysisNoteUpdate,
} from '../types';
import { annotationsApi, notesApi } from '../services/api';

// Annotation tool types for drawing
export type AnnotationTool =
  | 'SELECT'
  | 'TRENDLINE'
  | 'HORIZONTAL_LINE'
  | 'RECTANGLE'
  | 'TEXT'
  | 'ARROW'
  | 'FIBONACCI'
  | 'SUPPORT_RESISTANCE';

// Drawing state for active annotation being created
export interface DrawingState {
  isActive: boolean;
  tool: AnnotationTool;
  symbol: string;
  startPoint: { x: number; y: number } | null;
  currentPoint: { x: number; y: number } | null;
  tempAnnotation: Partial<AnnotationCreate> | null;
}

interface AnnotationState {
  // Annotations data
  annotations: Annotation[];
  annotationsMap: Record<string, Annotation[]>; // Keyed by symbol
  currentSymbol: string | null;

  // Loading states
  isLoadingAnnotations: boolean;
  isLoadingNotes: boolean;
  isSaving: boolean;

  // Error states
  annotationsError: string | null;
  notesError: string | null;

  // Analysis notes
  currentNote: AnalysisNote | null;

  // UI state
  showAnnotations: boolean;
  annotationsVisible: boolean;
  selectedAnnotationId: number | null;

  // Drawing state
  drawing: DrawingState;

  // Annotations actions
  loadAnnotations: (symbol: string) => Promise<void>;
  addAnnotation: (annotation: AnnotationCreate) => Promise<Annotation | null>;
  updateAnnotation: (id: number, updates: AnnotationUpdate) => Promise<void>;
  deleteAnnotation: (id: number) => Promise<void>;
  deleteAllAnnotations: (symbol: string) => Promise<void>;
  setSelectedAnnotation: (id: number | null) => void;
  toggleAnnotationsVisibility: () => void;
  setShowAnnotations: (show: boolean) => void;

  // Notes actions
  loadNote: (symbol: string) => Promise<void>;
  createNote: (note: AnalysisNoteCreate) => Promise<AnalysisNote | null>;
  updateNote: (symbol: string, updates: AnalysisNoteUpdate) => Promise<void>;
  deleteNote: (symbol: string) => Promise<void>;
  clearCurrentNote: () => void;

  // Drawing actions
  startDrawing: (tool: AnnotationTool, symbol: string) => void;
  stopDrawing: () => void;
  setDrawingPoint: (point: { x: number; y: number }) => void;
  setCurrentPoint: (point: { x: number; y: number }) => void;
  setTempAnnotation: (annotation: Partial<AnnotationCreate>) => void;

  // Utility actions
  clearAnnotationsForSymbol: (symbol: string) => void;
  setCurrentSymbol: (symbol: string | null) => void;
  resetErrors: () => void;
}

const initialDrawingState: DrawingState = {
  isActive: false,
  tool: 'SELECT',
  symbol: '',
  startPoint: null,
  currentPoint: null,
  tempAnnotation: null,
};

export const useAnnotationStore = create<AnnotationState>()(
  persist(
    (set, get) => ({
      // Initial state
      annotations: [],
      annotationsMap: {},
      currentSymbol: null,
      isLoadingAnnotations: false,
      isLoadingNotes: false,
      isSaving: false,
      annotationsError: null,
      notesError: null,
      currentNote: null,
      showAnnotations: true,
      annotationsVisible: true,
      selectedAnnotationId: null,
      drawing: initialDrawingState,

      // Annotations actions
      loadAnnotations: async (symbol: string) => {
        set({ isLoadingAnnotations: true, annotationsError: null, currentSymbol: symbol });
        try {
          const response: AnnotationListResponse = await annotationsApi.getAnnotations(symbol);
          const annotations = response.annotations || [];
          set({
            annotations,
            annotationsMap: {
              ...get().annotationsMap,
              [symbol]: annotations,
            },
            isLoadingAnnotations: false,
          });
        } catch (error) {
          set({
            annotationsError: error instanceof Error ? error.message : 'Failed to load annotations',
            isLoadingAnnotations: false,
            annotations: [],
          });
        }
      },

      addAnnotation: async (annotation: AnnotationCreate) => {
        set({ isSaving: true, annotationsError: null });
        try {
          const newAnnotation = await annotationsApi.createAnnotation(annotation);
          const symbol = annotation.symbol;
          set((state) => {
            const symbolAnnotations = state.annotationsMap[symbol] || [];
            const updatedAnnotations = [...symbolAnnotations, newAnnotation];
            return {
              annotations: updatedAnnotations,
              annotationsMap: {
                ...state.annotationsMap,
                [symbol]: updatedAnnotations,
              },
              isSaving: false,
            };
          });
          return newAnnotation;
        } catch (error) {
          set({
            annotationsError: error instanceof Error ? error.message : 'Failed to create annotation',
            isSaving: false,
          });
          return null;
        }
      },

      updateAnnotation: async (id: number, updates: AnnotationUpdate) => {
        set({ isSaving: true, annotationsError: null });
        try {
          const updatedAnnotation = await annotationsApi.updateAnnotation(id, updates);
          set((state) => {
            const symbol = state.currentSymbol;
            if (!symbol) return { isSaving: false };

            const symbolAnnotations = state.annotationsMap[symbol] || [];
            const updatedAnnotations = symbolAnnotations.map((a) =>
              a.id === id ? updatedAnnotation : a
            );
            return {
              annotations: updatedAnnotations,
              annotationsMap: {
                ...state.annotationsMap,
                [symbol]: updatedAnnotations,
              },
              isSaving: false,
            };
          });
        } catch (error) {
          set({
            annotationsError: error instanceof Error ? error.message : 'Failed to update annotation',
            isSaving: false,
          });
        }
      },

      deleteAnnotation: async (id: number) => {
        set({ isSaving: true, annotationsError: null });
        try {
          await annotationsApi.deleteAnnotation(id);
          set((state) => {
            const symbol = state.currentSymbol;
            if (!symbol) return { isSaving: false };

            const symbolAnnotations = state.annotationsMap[symbol] || [];
            const updatedAnnotations = symbolAnnotations.filter((a) => a.id !== id);
            return {
              annotations: updatedAnnotations,
              annotationsMap: {
                ...state.annotationsMap,
                [symbol]: updatedAnnotations,
              },
              selectedAnnotationId: state.selectedAnnotationId === id ? null : state.selectedAnnotationId,
              isSaving: false,
            };
          });
        } catch (error) {
          set({
            annotationsError: error instanceof Error ? error.message : 'Failed to delete annotation',
            isSaving: false,
          });
        }
      },

      deleteAllAnnotations: async (symbol: string) => {
        set({ isSaving: true, annotationsError: null });
        try {
          await annotationsApi.deleteAllAnnotations(symbol);
          set((state) => ({
            annotations: state.currentSymbol === symbol ? [] : state.annotations,
            annotationsMap: {
              ...state.annotationsMap,
              [symbol]: [],
            },
            selectedAnnotationId: null,
            isSaving: false,
          }));
        } catch (error) {
          set({
            annotationsError: error instanceof Error ? error.message : 'Failed to delete annotations',
            isSaving: false,
          });
        }
      },

      setSelectedAnnotation: (id: number | null) => {
        set({ selectedAnnotationId: id });
      },

      toggleAnnotationsVisibility: () => {
        set((state) => ({ annotationsVisible: !state.annotationsVisible }));
      },

      setShowAnnotations: (show: boolean) => {
        set({ showAnnotations: show });
      },

      // Notes actions
      loadNote: async (symbol: string) => {
        set({ isLoadingNotes: true, notesError: null });
        try {
          const note = await notesApi.getNote(symbol);
          set({ currentNote: note, isLoadingNotes: false });
        } catch (error) {
          // Note not found is not an error - just means no note exists yet
          if (error && typeof error === 'object' && 'response' in error) {
            const response = error.response as { status?: number };
            if (response.status === 404) {
              set({ currentNote: null, isLoadingNotes: false });
              return;
            }
          }
          set({
            notesError: error instanceof Error ? error.message : 'Failed to load note',
            isLoadingNotes: false,
            currentNote: null,
          });
        }
      },

      createNote: async (note: AnalysisNoteCreate) => {
        set({ isSaving: true, notesError: null });
        try {
          const newNote = await notesApi.createNote(note);
          set({ currentNote: newNote, isSaving: false });
          return newNote;
        } catch (error) {
          set({
            notesError: error instanceof Error ? error.message : 'Failed to create note',
            isSaving: false,
          });
          return null;
        }
      },

      updateNote: async (symbol: string, updates: AnalysisNoteUpdate) => {
        set({ isSaving: true, notesError: null });
        try {
          const updatedNote = await notesApi.updateNote(symbol, updates);
          set({ currentNote: updatedNote, isSaving: false });
        } catch (error) {
          set({
            notesError: error instanceof Error ? error.message : 'Failed to update note',
            isSaving: false,
          });
        }
      },

      deleteNote: async (symbol: string) => {
        set({ isSaving: true, notesError: null });
        try {
          await notesApi.deleteNote(symbol);
          set({ currentNote: null, isSaving: false });
        } catch (error) {
          set({
            notesError: error instanceof Error ? error.message : 'Failed to delete note',
            isSaving: false,
          });
        }
      },

      clearCurrentNote: () => {
        set({ currentNote: null });
      },

      // Drawing actions
      startDrawing: (tool: AnnotationTool, symbol: string) => {
        set({
          drawing: {
            ...initialDrawingState,
            isActive: true,
            tool,
            symbol,
          },
        });
      },

      stopDrawing: () => {
        set({
          drawing: initialDrawingState,
        });
      },

      setDrawingPoint: (point: { x: number; y: number }) => {
        set((state) => ({
          drawing: {
            ...state.drawing,
            startPoint: point,
          },
        }));
      },

      setCurrentPoint: (point: { x: number; y: number }) => {
        set((state) => ({
          drawing: {
            ...state.drawing,
            currentPoint: point,
          },
        }));
      },

      setTempAnnotation: (annotation: Partial<AnnotationCreate>) => {
        set((state) => ({
          drawing: {
            ...state.drawing,
            tempAnnotation: annotation,
          },
        }));
      },

      // Utility actions
      clearAnnotationsForSymbol: (symbol: string) => {
        set((state) => {
          const { [symbol]: _, ...rest } = state.annotationsMap;
          return {
            annotationsMap: rest,
            annotations: state.currentSymbol === symbol ? [] : state.annotations,
          };
        });
      },

      setCurrentSymbol: (symbol: string | null) => {
        set({ currentSymbol: symbol });
      },

      resetErrors: () => {
        set({ annotationsError: null, notesError: null });
      },
    }),
    {
      name: 'annotation-storage',
      partialize: (state) => ({
        // Only persist these fields to localStorage
        annotationsMap: state.annotationsMap,
        showAnnotations: state.showAnnotations,
        // Don't persist: loading states, errors, current symbol, drawing state, selected annotation
      }),
    }
  )
);
