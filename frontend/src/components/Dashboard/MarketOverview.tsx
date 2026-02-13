import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { stockApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';

const NIFTY_SYMBOL = '^NSEI';

export function MarketOverview() {
  const { data: quote, isLoading } = useQuery({
    queryKey: ['quote', NIFTY_SYMBOL],
    queryFn: () => stockApi.getQuote(NIFTY_SYMBOL),
    refetchInterval: 60000,
  });

  const isPositive = quote && quote.change >= 0;

  return (
    <div className="card">
      <h3 className="card-header">Market Overview</h3>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : quote ? (
        <div className="space-y-5">
          {/* Main Index */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Nifty 50
              </div>
              <div className="text-3xl font-bold font-mono-num text-slate-100 mt-1">
                {quote.last_price.toLocaleString('en-IN', {
                  maximumFractionDigits: 2,
                })}
              </div>
            </div>
            <div
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${isPositive
                  ? 'bg-emerald-500/10 border border-emerald-500/20'
                  : 'bg-red-500/10 border border-red-500/20'
                }`}
            >
              {isPositive ? (
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-400" />
              )}
              <div className="text-right">
                <div
                  className={`font-semibold font-mono-num text-sm ${isPositive ? 'text-emerald-400' : 'text-red-400'
                    }`}
                >
                  {isPositive ? '+' : ''}
                  {quote.change.toFixed(2)}
                </div>
                <div
                  className={`text-xs font-mono-num ${isPositive ? 'text-emerald-500' : 'text-red-500'
                    }`}
                >
                  {isPositive ? '+' : ''}
                  {quote.change_percent.toFixed(2)}%
                </div>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/30">
              <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                Day High
              </div>
              <div className="font-semibold font-mono-num text-sm text-slate-200 mt-1">
                {quote.day_high.toLocaleString('en-IN', {
                  maximumFractionDigits: 2,
                })}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/30">
              <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                Day Low
              </div>
              <div className="font-semibold font-mono-num text-sm text-slate-200 mt-1">
                {quote.day_low.toLocaleString('en-IN', {
                  maximumFractionDigits: 2,
                })}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/30">
              <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                Volume
              </div>
              <div className="font-semibold font-mono-num text-sm text-slate-200 mt-1">
                {(quote.volume / 1000000).toFixed(2)}M
              </div>
            </div>
          </div>

          {/* Day Range Bar */}
          <div>
            <div className="flex justify-between text-[10px] font-medium text-slate-500 mb-1.5 uppercase tracking-wider">
              <span>Day Range</span>
              <span className="font-mono-num normal-case">
                {((quote.last_price - quote.day_low) /
                  (quote.day_high - quote.day_low) *
                  100
                ).toFixed(0)}
                % of range
              </span>
            </div>
            <div className="h-1.5 bg-slate-800/60 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${isPositive
                    ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                    : 'bg-gradient-to-r from-red-500 to-red-400'
                  }`}
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(
                      0,
                      ((quote.last_price - quote.day_low) /
                        (quote.day_high - quote.day_low)) *
                      100
                    )
                  )}%`,
                }}
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500 text-sm">
          Unable to load market data
        </div>
      )}
    </div>
  );
}
