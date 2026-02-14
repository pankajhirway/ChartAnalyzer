import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Trash2, RefreshCw, Eye, Star, Check, Square } from 'lucide-react';
import { watchlistApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { WatchlistItem } from '../../types';

export function Watchlist() {
  const queryClient = useQueryClient();
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set());

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['watchlist'],
    queryFn: watchlistApi.getWatchlist,
  });

  const removeMutation = useMutation({
    mutationFn: watchlistApi.removeItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });

  const bulkRemoveMutation = useMutation({
    mutationFn: (symbols: string[]) => watchlistApi.bulkRemove(symbols),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
      setSelectedSymbols(new Set());
    },
  });

  const handleRemove = (symbol: string) => {
    if (confirm(`Remove ${symbol} from watchlist?`)) {
      removeMutation.mutate(symbol);
    }
  };

  const handleBulkRemove = () => {
    if (selectedSymbols.size === 0) return;
    const symbols = Array.from(selectedSymbols);
    if (confirm(`Remove ${symbols.length} ${symbols.length === 1 ? 'stock' : 'stocks'} from watchlist?`)) {
      bulkRemoveMutation.mutate(symbols);
    }
  };

  // Selection handlers
  const handleToggleSelect = (symbol: string) => {
    setSelectedSymbols((prev) => {
      const next = new Set(prev);
      if (next.has(symbol)) {
        next.delete(symbol);
      } else {
        next.add(symbol);
      }
      return next;
    });
  };

  const handleToggleSelectAll = () => {
    if (data && selectedSymbols.size === data.items.length && data.items.length > 0) {
      setSelectedSymbols(new Set());
    } else {
      setSelectedSymbols(new Set(data?.items.map((item: WatchlistItem) => item.symbol) || []));
    }
  };

  const handleClearSelection = () => {
    setSelectedSymbols(new Set());
  };

  const allSelected = data && data.items.length > 0 && selectedSymbols.size === data.items.length;
  const someSelected = selectedSymbols.size > 0 && data && selectedSymbols.size < data.items.length;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Star className="w-4 h-4 text-amber-400" />
          <h3 className="card-header mb-0">Watchlist</h3>
        </div>
        <div className="flex items-center gap-1">
          {data && data.items.length > 0 && (
            <button
              onClick={handleToggleSelectAll}
              className="p-1.5 hover:bg-slate-800/60 rounded-lg transition-colors"
              title={allSelected ? 'Deselect all' : 'Select all'}
            >
              {allSelected ? (
                <Check className="w-3.5 h-3.5 text-blue-400" />
              ) : someSelected ? (
                <div className="relative w-3.5 h-3.5">
                  <Square className="w-3.5 h-3.5 text-blue-400 absolute" />
                  <div className="absolute inset-0.5 bg-blue-400 rounded-sm" />
                </div>
              ) : (
                <div className="w-3.5 h-3.5 border-2 border-slate-600 rounded-sm" />
              )}
            </button>
          )}
          <button
            onClick={() => refetch()}
            className="p-1.5 hover:bg-slate-800/60 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300 transition-colors" />
          </button>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {selectedSymbols.size > 0 && (
        <div className="mb-4 p-3 rounded-lg bg-blue-500/8 border border-blue-500/20 flex items-center justify-between animate-fade-in-down">
          <div className="flex items-center gap-3">
            <span className="text-sm text-blue-300 font-medium">
              {selectedSymbols.size} {selectedSymbols.size === 1 ? 'stock' : 'stocks'} selected
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleBulkRemove}
              disabled={bulkRemoveMutation.isPending}
              className="btn btn-sm bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 flex items-center gap-2"
            >
              {bulkRemoveMutation.isPending ? (
                <LoadingSpinner size="sm" />
              ) : (
                <Trash2 className="w-3.5 h-3.5" />
              )}
              Remove
            </button>
            <button
              onClick={handleClearSelection}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-lg transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="divide-y divide-slate-800/60">
          {data.items.map((item: WatchlistItem) => {
            const isSelected = selectedSymbols.has(item.symbol);
            return (
              <div
                key={item.symbol}
                className={`py-3 flex items-center justify-between group hover:bg-slate-800/20 transition-colors ${
                  isSelected ? 'bg-blue-500/5' : ''
                }`}
              >
                <div className="flex items-center space-x-3 flex-1">
                  <button
                    onClick={() => handleToggleSelect(item.symbol)}
                    className={`p-1.5 rounded-md transition-colors ${
                      isSelected
                        ? 'bg-blue-500/20 hover:bg-blue-500/30'
                        : 'hover:bg-slate-800/60'
                    }`}
                    title={isSelected ? 'Deselect' : 'Select'}
                  >
                    {isSelected ? (
                      <Check className="w-3.5 h-3.5 text-blue-400" />
                    ) : (
                      <div className="w-3.5 h-3.5 border-2 border-slate-600 rounded-sm" />
                    )}
                  </button>
                  <Link
                    to={`/stock/${item.symbol}`}
                    className="flex-1 flex items-center space-x-3 hover:text-blue-400 transition-colors"
                  >
                    <div className="p-1.5 rounded-md bg-slate-800/50 border border-slate-700/30">
                      <Eye className="w-3.5 h-3.5 text-slate-500" />
                    </div>
                    <div>
                      <div className="font-medium text-sm text-slate-200">
                        {item.symbol}
                      </div>
                      <div className="text-xs text-slate-500">
                        {item.company_name || 'N/A'}
                      </div>
                    </div>
                  </Link>
                </div>
                <button
                  onClick={() => handleRemove(item.symbol)}
                  className="p-1.5 text-slate-600 hover:text-red-400 hover:bg-red-500/10 rounded-md opacity-0 group-hover:opacity-100 transition-all duration-200"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-8">
          <Star className="w-8 h-8 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No stocks in watchlist</p>
          <p className="text-slate-600 text-xs mt-1">
            Search for stocks and add them to track
          </p>
        </div>
      )}
    </div>
  );
}
