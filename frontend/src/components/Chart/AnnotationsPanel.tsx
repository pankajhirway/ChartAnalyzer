import { Trash2, RefreshCw, Eye, EyeOff, Minus, LineChart } from 'lucide-react';
import { useAnnotationStore } from '../../store/annotationStore';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { Annotation, AnnotationType } from '../../types';
import { formatDistanceToNow } from 'date-fns';

// Helper function to get annotation type display name
function getAnnotationTypeName(type: AnnotationType): string {
  switch (type) {
    case 'TRENDLINE':
      return 'Trendline';
    case 'HORIZONTAL_LINE':
      return 'Horizontal Line';
    case 'RECTANGLE':
      return 'Rectangle';
    case 'TEXT':
      return 'Text';
    case 'ARROW':
      return 'Arrow';
    case 'FIBONACCI':
      return 'Fibonacci';
    case 'SUPPORT_RESISTANCE':
      return 'Support/Resistance';
    default:
      return type;
  }
}

// Helper function to get annotation type icon color
function getAnnotationColorClass(color: string): string {
  const colorMap: Record<string, string> = {
    '#FF0000': 'bg-red-500',
    '#00FF00': 'bg-green-500',
    '#0000FF': 'bg-blue-500',
    '#FFFF00': 'bg-yellow-500',
    '#FFA500': 'bg-orange-500',
    '#800080': 'bg-purple-500',
    '#00FFFF': 'bg-cyan-500',
    '#FF00FF': 'bg-fuchsia-500',
    '#FFFFFF': 'bg-white',
    '#000000': 'bg-black',
  };
  return colorMap[color] || 'bg-slate-500';
}

interface AnnotationsPanelProps {
  symbol: string;
}

export function AnnotationsPanel({ symbol }: AnnotationsPanelProps) {
  const {
    annotations,
    isLoadingAnnotations,
    annotationsError,
    deleteAnnotation,
    loadAnnotations,
    updateAnnotation,
    annotationsVisible,
    toggleAnnotationsVisibility,
  } = useAnnotationStore();

  const handleDelete = (id: number, title?: string) => {
    const confirmMessage = title
      ? `Delete annotation "${title}"?`
      : 'Delete this annotation?';
    if (confirm(confirmMessage)) {
      deleteAnnotation(id);
    }
  };

  const handleToggleVisibility = (annotation: Annotation) => {
    updateAnnotation(annotation.id, { visible: !annotation.visible });
  };

  const handleRefresh = () => {
    loadAnnotations(symbol);
  };

  // Filter annotations for current symbol
  const symbolAnnotations = annotations.filter(a => a.symbol === symbol);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <LineChart className="w-4 h-4 text-blue-400" />
          <h3 className="card-header mb-0">Annotations</h3>
          {symbolAnnotations.length > 0 && (
            <span className="text-xs text-slate-500 bg-slate-800/50 px-2 py-0.5 rounded-full">
              {symbolAnnotations.length}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={toggleAnnotationsVisibility}
            className="p-1.5 hover:bg-slate-800/60 rounded-lg transition-colors"
            title={annotationsVisible ? 'Hide all annotations' : 'Show all annotations'}
          >
            {annotationsVisible ? (
              <Eye className="w-3.5 h-3.5 text-blue-400" />
            ) : (
              <EyeOff className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300 transition-colors" />
            )}
          </button>
          <button
            onClick={handleRefresh}
            className="p-1.5 hover:bg-slate-800/60 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300 transition-colors" />
          </button>
        </div>
      </div>

      {annotationsError && (
        <div className="mb-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-red-400 text-xs">{annotationsError}</p>
        </div>
      )}

      {isLoadingAnnotations ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : symbolAnnotations.length > 0 ? (
        <div className="divide-y divide-slate-800/60 max-h-[400px] overflow-y-auto">
          {symbolAnnotations.map((annotation: Annotation) => (
            <div
              key={annotation.id}
              className={`py-3 flex items-center justify-between group ${!annotation.visible ? 'opacity-50' : ''}`}
            >
              <div className="flex-1 flex items-center space-x-3">
                <div className="p-1.5 rounded-md bg-slate-800/50 border border-slate-700/30">
                  <Minus
                    className={`w-3.5 h-3.5 ${annotation.visible ? 'text-slate-500' : 'text-slate-600'}`}
                    style={{ color: annotation.visible ? annotation.color : undefined }}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-sm text-slate-200">
                      {annotation.title || getAnnotationTypeName(annotation.annotation_type)}
                    </span>
                    <div
                      className={`w-2 h-2 rounded-full ${getAnnotationColorClass(annotation.color)}`}
                      title={annotation.color}
                    />
                  </div>
                  <div className="flex items-center space-x-2 mt-0.5">
                    <span className="text-xs text-slate-500">
                      {getAnnotationTypeName(annotation.annotation_type)}
                    </span>
                    {annotation.notes && (
                      <>
                        <span className="text-slate-700">•</span>
                        <span className="text-xs text-slate-600 truncate max-w-[150px]" title={annotation.notes}>
                          {annotation.notes}
                        </span>
                      </>
                    )}
                  </div>
                  {annotation.created_at && (
                    <div className="text-xs text-slate-600 mt-0.5">
                      {formatDistanceToNow(new Date(annotation.created_at), { addSuffix: true })}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => handleToggleVisibility(annotation)}
                  className="p-1.5 text-slate-600 hover:text-blue-400 hover:bg-blue-500/10 rounded-md opacity-0 group-hover:opacity-100 transition-all duration-200"
                  title={annotation.visible ? 'Hide' : 'Show'}
                >
                  {annotation.visible ? (
                    <Eye className="w-3.5 h-3.5" />
                  ) : (
                    <EyeOff className="w-3.5 h-3.5" />
                  )}
                </button>
                <button
                  onClick={() => handleDelete(annotation.id, annotation.title)}
                  className="p-1.5 text-slate-600 hover:text-red-400 hover:bg-red-500/10 rounded-md opacity-0 group-hover:opacity-100 transition-all duration-200"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <LineChart className="w-8 h-8 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No annotations yet</p>
          <p className="text-slate-600 text-xs mt-1">
            Use the drawing tools to add annotations to the chart
          </p>
        </div>
      )}
    </div>
  );
}
