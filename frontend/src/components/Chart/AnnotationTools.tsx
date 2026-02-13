import { MousePointer2, TrendingUp, Square, Type, Minus, ArrowRight, Activity, Layers, Trash2, Eye, EyeOff } from 'lucide-react';
import { useAnnotationStore, type AnnotationTool } from '../../store/annotationStore';

const TOOL_BUTTONS: { tool: AnnotationTool; icon: any; label: string }[] = [
  { tool: 'SELECT', icon: MousePointer2, label: 'Select' },
  { tool: 'TRENDLINE', icon: TrendingUp, label: 'Trendline' },
  { tool: 'HORIZONTAL_LINE', icon: Minus, label: 'Horizontal' },
  { tool: 'RECTANGLE', icon: Square, label: 'Rectangle' },
  { tool: 'TEXT', icon: Type, label: 'Text' },
  { tool: 'ARROW', icon: ArrowRight, label: 'Arrow' },
  { tool: 'FIBONACCI', icon: Activity, label: 'Fibonacci' },
  { tool: 'SUPPORT_RESISTANCE', icon: Layers, label: 'Support/Resistance' },
];

interface AnnotationToolsProps {
  symbol: string;
}

export function AnnotationTools({ symbol }: AnnotationToolsProps) {
  const {
    drawing,
    startDrawing,
    stopDrawing,
    deleteAllAnnotations,
    annotationsVisible,
    toggleAnnotationsVisibility,
  } = useAnnotationStore();

  const handleToolClick = (tool: AnnotationTool) => {
    if (drawing.isActive && drawing.tool === tool) {
      // Toggle off if clicking the same active tool
      stopDrawing();
    } else if (tool === 'SELECT') {
      // Just stop drawing for select tool
      stopDrawing();
    } else {
      // Start drawing with the selected tool
      startDrawing(tool, symbol);
    }
  };

  const handleClearAll = () => {
    if (confirm('Are you sure you want to delete all annotations for this stock?')) {
      deleteAllAnnotations(symbol);
    }
  };

  const handleToggleVisibility = () => {
    toggleAnnotationsVisibility();
  };

  return (
    <div className="flex items-center space-x-2 p-2 bg-slate-800/40 rounded-lg border border-slate-700/50 backdrop-blur-sm">
      {/* Drawing Tools */}
      <div className="flex items-center space-x-1">
        {TOOL_BUTTONS.map(({ tool, icon: Icon, label }) => {
          const isActive = drawing.isActive && drawing.tool === tool;
          const isSelectTool = tool === 'SELECT';

          return (
            <button
              key={tool}
              onClick={() => handleToolClick(tool)}
              className={`
                relative group p-2 rounded-lg transition-all duration-200
                ${isActive
                  ? 'bg-blue-500/20 text-blue-400 ring-1 ring-blue-500/50'
                  : isSelectTool
                    ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/40'
                }
              `}
              title={label}
            >
              <Icon className="w-4 h-4 transition-transform duration-200 group-hover:scale-110" />
              {isActive && (
                <div className="absolute inset-0 bg-blue-400/10 rounded-lg" />
              )}
            </button>
          );
        })}
      </div>

      {/* Separator */}
      <div className="w-px h-6 bg-slate-700/50" />

      {/* Visibility Toggle */}
      <button
        onClick={handleToggleVisibility}
        className={`
          relative group p-2 rounded-lg transition-all duration-200
          ${annotationsVisible
            ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/40'
            : 'text-slate-500 hover:text-slate-300 hover:bg-slate-700/40'
          }
        `}
        title={annotationsVisible ? 'Hide Annotations' : 'Show Annotations'}
      >
        {annotationsVisible ? (
          <Eye className="w-4 h-4 transition-transform duration-200 group-hover:scale-110" />
        ) : (
          <EyeOff className="w-4 h-4 transition-transform duration-200 group-hover:scale-110" />
        )}
      </button>

      {/* Clear All Button */}
      <button
        onClick={handleClearAll}
        className="relative group p-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all duration-200"
        title="Clear All Annotations"
      >
        <Trash2 className="w-4 h-4 transition-transform duration-200 group-hover:scale-110" />
      </button>
    </div>
  );
}
