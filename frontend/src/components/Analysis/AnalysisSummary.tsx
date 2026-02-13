import type { AnalysisResult } from '../../types';
import { CheckCircle, XCircle, AlertTriangle, Shapes } from 'lucide-react';

interface AnalysisSummaryProps {
  analysis: AnalysisResult;
}

export function AnalysisSummary({ analysis }: AnalysisSummaryProps) {
  return (
    <div className="card">
      <h3 className="card-header">Analysis Summary</h3>

      <div className="space-y-5">
        {/* Bullish Factors */}
        {analysis.bullish_factors.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-emerald-400 mb-2.5 flex items-center uppercase tracking-wider">
              <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
              Bullish Factors
            </h4>
            <ul className="space-y-1.5">
              {analysis.bullish_factors.map((factor, index) => (
                <li
                  key={index}
                  className="text-sm text-slate-400 flex items-start"
                >
                  <span className="text-emerald-500/60 mr-2 mt-1 flex-shrink-0">•</span>
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Bearish Factors */}
        {analysis.bearish_factors.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-red-400 mb-2.5 flex items-center uppercase tracking-wider">
              <XCircle className="w-3.5 h-3.5 mr-1.5" />
              Bearish Factors
            </h4>
            <ul className="space-y-1.5">
              {analysis.bearish_factors.map((factor, index) => (
                <li
                  key={index}
                  className="text-sm text-slate-400 flex items-start"
                >
                  <span className="text-red-500/60 mr-2 mt-1 flex-shrink-0">•</span>
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {analysis.warnings.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-amber-400 mb-2.5 flex items-center uppercase tracking-wider">
              <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
              Warnings
            </h4>
            <ul className="space-y-1.5">
              {analysis.warnings.map((warning, index) => (
                <li
                  key={index}
                  className="text-sm text-slate-400 flex items-start"
                >
                  <span className="text-amber-500/60 mr-2 mt-1 flex-shrink-0">•</span>
                  {warning}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Patterns */}
        {analysis.detected_patterns.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-300 mb-2.5 flex items-center uppercase tracking-wider">
              <Shapes className="w-3.5 h-3.5 mr-1.5" />
              Detected Patterns
            </h4>
            <div className="flex flex-wrap gap-2">
              {analysis.detected_patterns.map((pattern, index) => (
                <span
                  key={index}
                  className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${pattern.bullish
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-red-500/10 text-red-400 border-red-500/20'
                    }`}
                >
                  {pattern.pattern_name}
                  <span className="ml-1.5 text-slate-500 font-mono-num">
                    {pattern.completion_pct.toFixed(0)}%
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Support/Resistance */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800/60">
          <div>
            <h4 className="text-[10px] font-semibold text-slate-400 mb-2 uppercase tracking-wider">
              Support Levels
            </h4>
            <div className="space-y-1.5">
              {analysis.support_levels.slice(0, 3).map((level, index) => (
                <div
                  key={index}
                  className="text-sm text-slate-400 flex justify-between"
                >
                  <span className="font-mono-num text-emerald-400/80">
                    ₹{level.price.toLocaleString('en-IN')}
                  </span>
                  <span className="text-[10px] text-slate-600">
                    {level.description}
                  </span>
                </div>
              ))}
              {analysis.support_levels.length === 0 && (
                <span className="text-xs text-slate-600">No significant levels</span>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-[10px] font-semibold text-slate-400 mb-2 uppercase tracking-wider">
              Resistance Levels
            </h4>
            <div className="space-y-1.5">
              {analysis.resistance_levels.slice(0, 3).map((level, index) => (
                <div
                  key={index}
                  className="text-sm text-slate-400 flex justify-between"
                >
                  <span className="font-mono-num text-red-400/80">
                    ₹{level.price.toLocaleString('en-IN')}
                  </span>
                  <span className="text-[10px] text-slate-600">
                    {level.description}
                  </span>
                </div>
              ))}
              {analysis.resistance_levels.length === 0 && (
                <span className="text-xs text-slate-600">No significant levels</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
