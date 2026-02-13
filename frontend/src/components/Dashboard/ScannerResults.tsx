import { useState } from 'react';
import { RefreshCw, ChevronUp, ChevronDown } from 'lucide-react';
import type { ScanResult, SignalType, ConvictionLevel } from '../../types';

interface ScannerResultsProps {
  results: ScanResult[];
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

type SortField = 'symbol' | 'current_price' | 'composite_score' | 'signal' | 'weinstein_stage' | 'pattern_count';

interface SortState {
  field: SortField;
  direction: 'asc' | 'desc';
}

export function ScannerResults({ results, onRefresh, isRefreshing = false }: ScannerResultsProps) {
  const [sortState, setSortState] = useState<SortState>({ field: 'composite_score', direction: 'desc' });

  const handleSort = (field: SortField) => {
    setSortState((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
  };

  const sortedResults = [...results].sort((a, b) => {
    const { field, direction } = sortState;
    const multiplier = direction === 'asc' ? 1 : -1;

    switch (field) {
      case 'symbol':
        return multiplier * a.symbol.localeCompare(b.symbol);
      case 'current_price':
        return multiplier * (a.current_price - b.current_price);
      case 'composite_score':
        return multiplier * (a.composite_score - b.composite_score);
      case 'signal':
        return multiplier * a.signal.localeCompare(b.signal);
      case 'weinstein_stage':
        return multiplier * (a.weinstein_stage - b.weinstein_stage);
      case 'pattern_count':
        return multiplier * (a.patterns.length - b.patterns.length);
      default:
        return 0;
    }
  });

  const renderSortIcon = (field: SortField) => {
    if (sortState.field !== field) return null;
    return sortState.direction === 'asc' ? (
      <ChevronUp className="w-3 h-3 inline-block ml-1" />
    ) : (
      <ChevronDown className="w-3 h-3 inline-block ml-1" />
    );
  };

  return (
    <div className="card animate-fade-in-up" style={{ animationDelay: '150ms' }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-header mb-0">
          Scan Results{' '}
          <span className="text-slate-500 font-normal">({results.length})</span>
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 hover:bg-slate-800/60 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Refresh scan"
          >
            <RefreshCw className={`w-4 h-4 text-slate-500 hover:text-slate-300 transition-colors ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        )}
      </div>

      <div className="overflow-x-auto -mx-5 px-5">
        <table className="w-full">
          <thead>
            <tr className="text-left text-[10px] font-medium text-slate-500 uppercase tracking-wider border-b border-slate-800/60">
              <th className="pb-3 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('symbol')}>
                Symbol {renderSortIcon('symbol')}
              </th>
              <th className="pb-3 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('current_price')}>
                Price {renderSortIcon('current_price')}
              </th>
              <th className="pb-3 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('composite_score')}>
                Score {renderSortIcon('composite_score')}
              </th>
              <th className="pb-3 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('signal')}>
                Signal {renderSortIcon('signal')}
              </th>
              <th className="pb-3 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('weinstein_stage')}>
                Stage {renderSortIcon('weinstein_stage')}
              </th>
              <th className="pb-3 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('pattern_count')}>
                Patterns {renderSortIcon('pattern_count')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {sortedResults.map((result: ScanResult) => (
              <tr
                key={result.symbol}
                className="group hover:bg-slate-800/30 cursor-pointer transition-colors duration-150"
                onClick={() => (window.location.href = `/stock/${result.symbol}`)}
              >
                <td className="py-3.5">
                  <div className="font-medium text-sm text-slate-200 group-hover:text-blue-400 transition-colors">
                    {result.symbol}
                  </div>
                  <div className="text-xs text-slate-500">{result.company_name}</div>
                </td>
                <td className="py-3.5">
                  <span className="font-mono-num text-sm text-slate-300">
                    ₹{result.current_price.toLocaleString('en-IN')}
                  </span>
                </td>
                <td className="py-3.5">
                  <div className="flex items-center space-x-2">
                    <div className="w-16 h-1.5 bg-slate-800/60 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          result.composite_score >= 70
                            ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                            : result.composite_score >= 50
                              ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                              : 'bg-gradient-to-r from-red-500 to-red-400'
                        }`}
                        style={{ width: `${result.composite_score}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold font-mono-num text-slate-400">
                      {result.composite_score.toFixed(0)}
                    </span>
                  </div>
                </td>
                <td className="py-3.5">
                  <SignalBadge signal={result.signal} conviction={result.conviction} />
                </td>
                <td className="py-3.5">
                  <StageBadge stage={result.weinstein_stage} />
                </td>
                <td className="py-3.5">
                  <div className="text-xs text-slate-500">
                    {result.patterns.length > 0 ? result.patterns.slice(0, 2).join(', ') : '—'}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SignalBadge({ signal, conviction }: { signal: SignalType; conviction: ConvictionLevel }) {
  const colors: Record<SignalType, string> = {
    BUY: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    SELL: 'bg-red-500/15 text-red-400 border-red-500/20',
    HOLD: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    AVOID: 'bg-slate-500/15 text-slate-400 border-slate-500/20',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border ${colors[signal]}`}>
      {signal}
      {conviction === 'HIGH' && ' '}
      {conviction === 'HIGH' && <span className="ml-0.5">⭐</span>}
    </span>
  );
}

function StageBadge({ stage }: { stage: number }) {
  const colors: Record<number, string> = {
    1: 'bg-slate-500/15 text-slate-400 border-slate-500/20',
    2: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    3: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    4: 'bg-red-500/15 text-red-400 border-red-500/20',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border ${colors[stage]}`}>
      S{stage}
    </span>
  );
}
