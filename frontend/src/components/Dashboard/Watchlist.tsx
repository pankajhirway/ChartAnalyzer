import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Trash2, RefreshCw, Eye, Star } from 'lucide-react';
import { watchlistApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { WatchlistItem } from '../../types';

export function Watchlist() {
  const queryClient = useQueryClient();

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

  const handleRemove = (symbol: string) => {
    if (confirm(`Remove ${symbol} from watchlist?`)) {
      removeMutation.mutate(symbol);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Star className="w-4 h-4 text-amber-400" />
          <h3 className="card-header mb-0">Watchlist</h3>
        </div>
        <button
          onClick={() => refetch()}
          className="p-1.5 hover:bg-slate-800/60 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300 transition-colors" />
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="divide-y divide-slate-800/60">
          {data.items.map((item: WatchlistItem) => (
            <div
              key={item.symbol}
              className="py-3 flex items-center justify-between group"
            >
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
              <button
                onClick={() => handleRemove(item.symbol)}
                className="p-1.5 text-slate-600 hover:text-red-400 hover:bg-red-500/10 rounded-md opacity-0 group-hover:opacity-100 transition-all duration-200"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
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
