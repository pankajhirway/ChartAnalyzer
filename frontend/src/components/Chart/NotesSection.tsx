import { useEffect, useState } from 'react';
import { FileText, Save, Trash2, Plus, Loader2 } from 'lucide-react';
import { useAnnotationStore } from '../../store/annotationStore';

interface NotesSectionProps {
  symbol: string;
}

export function NotesSection({ symbol }: NotesSectionProps) {
  const {
    currentNote,
    isLoadingNotes,
    isSaving,
    notesError,
    loadNote,
    createNote,
    updateNote,
    deleteNote,
    clearCurrentNote,
  } = useAnnotationStore();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [category, setCategory] = useState('');
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);

  // Load note when symbol changes
  useEffect(() => {
    if (symbol) {
      loadNote(symbol);
    }
    return () => {
      clearCurrentNote();
    };
  }, [symbol, loadNote, clearCurrentNote]);

  // Update form fields when currentNote changes
  useEffect(() => {
    if (currentNote) {
      setTitle(currentNote.title);
      setContent(currentNote.content);
      setTags(currentNote.tags || '');
      setCategory(currentNote.category || '');
    } else {
      setTitle('');
      setContent('');
      setTags('');
      setCategory('');
    }
  }, [currentNote]);

  const handleSave = async () => {
    if (!symbol) return;

    if (currentNote) {
      // Update existing note
      await updateNote(symbol, { title, content, tags, category });
    } else {
      // Create new note
      if (title.trim() || content.trim()) {
        await createNote({
          symbol,
          title: title.trim() || `${symbol} Analysis Notes`,
          content,
          tags,
          category,
        });
      }
    }
    setShowSaveSuccess(true);
    setTimeout(() => setShowSaveSuccess(false), 2000);
  };

  const handleDelete = async () => {
    if (currentNote && symbol) {
      if (confirm('Are you sure you want to delete this note?')) {
        await deleteNote(symbol);
      }
    }
  };

  const handleNewNote = () => {
    setTitle('');
    setContent('');
    setTags('');
    setCategory('');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoadingNotes) {
    return (
      <div className="card">
        <h3 className="card-header">Analysis Notes</h3>
        <div className="flex justify-center items-center py-12">
          <Loader2 className="w-6 h-6 text-slate-500 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-header flex items-center">
          <FileText className="w-4 h-4 mr-2 text-slate-400" />
          Analysis Notes
        </h3>
        {currentNote && (
          <button
            onClick={handleNewNote}
            className="p-1.5 hover:bg-slate-800/60 rounded-lg transition-colors"
            title="Create new note"
          >
            <Plus className="w-4 h-4 text-slate-400" />
          </button>
        )}
      </div>

      {notesError && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-400">{notesError}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Title Input */}
        <div>
          <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={`${symbol} Analysis Notes`}
            className="w-full px-3 py-2 bg-slate-900/40 border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-colors"
          />
        </div>

        {/* Content Textarea */}
        <div>
          <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Notes
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Add your analysis notes, trade rationale, observations..."
            rows={8}
            className="w-full px-3 py-2 bg-slate-900/40 border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-colors resize-y"
          />
        </div>

        {/* Tags and Category */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Tags
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="comma, separated, tags"
              className="w-full px-3 py-2 bg-slate-900/40 border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-colors"
            />
          </div>
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900/40 border border-slate-700/50 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-colors"
            >
              <option value="">None</option>
              <option value="technical">Technical</option>
              <option value="fundamental">Fundamental</option>
              <option value="trade-setup">Trade Setup</option>
              <option value="risk-management">Risk Management</option>
              <option value="general">General</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
          <div className="flex items-center space-x-2">
            {currentNote && (
              <span className="text-xs text-slate-600">
                Last updated: {formatDate(currentNote.updated_at)}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {currentNote && (
              <button
                onClick={handleDelete}
                disabled={isSaving}
                className="px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete</span>
              </button>
            )}
            <button
              onClick={handleSave}
              disabled={isSaving || (!title.trim() && !content.trim())}
              className="px-3 py-1.5 text-xs font-medium bg-blue-500/15 text-blue-400 hover:bg-blue-500/25 border border-blue-500/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1.5"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : showSaveSuccess ? (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Saved!</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Note</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Empty State */}
        {!currentNote && !title && !content && (
          <div className="text-center py-8 border border-dashed border-slate-700/50 rounded-lg">
            <FileText className="w-10 h-10 text-slate-700 mx-auto mb-3" />
            <p className="text-sm text-slate-500 mb-1">No notes yet</p>
            <p className="text-xs text-slate-600">Add your analysis notes and trade rationale</p>
          </div>
        )}
      </div>
    </div>
  );
}
