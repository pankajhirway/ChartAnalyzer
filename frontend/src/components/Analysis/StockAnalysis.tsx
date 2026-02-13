import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Plus, RefreshCw, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { analysisApi, watchlistApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { AnalysisSummary } from './AnalysisSummary';
import { ScoreCard } from './ScoreCard';
import { SignalDisplay } from './SignalDisplay';
import { TradeSuggestion } from './TradeSuggestion';
import { PriceChart } from '../Chart/PriceChart';

export function StockAnalysis() {
  const { symbol } = useParams<{ symbol: string }>();

  const { data: analysis, isLoading, refetch, isFetching, error } = useQuery({
    queryKey: ['analysis', symbol],
    queryFn: () => analysisApi.analyze(symbol!),
    enabled: !!symbol,
    retry: 1,
  });

  const addToWatchlist = async () => {
    if (symbol) {
      try {
        await watchlistApi.addItem(symbol);
        alert(`${symbol} added to watchlist`);
      } catch (error) {
        alert('Failed to add to watchlist');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-slate-400 text-sm">Analyzing {symbol}...</p>
          <p className="text-slate-600 text-xs mt-1">Running strategy analysis</p>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="text-center py-16">
        <div className="w-14 h-14 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-7 h-7 text-red-400" />
        </div>
        <p className="text-slate-300 mb-2">Unable to analyze {symbol}</p>
        <p className="text-sm text-slate-500 mb-6 max-w-sm mx-auto">
          {error ? String(error) : 'No analysis data available'}
        </p>
        <div className="flex items-center justify-center space-x-3">
          <button
            onClick={() => refetch()}
            className="btn btn-primary"
          >
            Try Again
          </button>
          <Link to="/" className="btn btn-secondary">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center space-x-4">
          <Link
            to="/"
            className="p-2 hover:bg-slate-800/60 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
              {analysis.symbol}
            </h1>
            {analysis.company_name && (
              <p className="text-sm text-slate-500">{analysis.company_name}</p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={addToWatchlist}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Watch</span>
          </button>
        </div>
      </div>

      {/* Price and Signal */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4" style={{ animationDelay: '75ms' }}>
        {/* Current Price */}
        <div className="card">
          <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
            Current Price
          </div>
          <div className="text-3xl font-bold font-mono-num text-slate-100 mt-1">
            ₹{analysis.current_price?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || 'N/A'}
          </div>
          <div className="flex items-center space-x-2 mt-2">
            <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border ${analysis.primary_trend === 'BULLISH'
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20'
                : analysis.primary_trend === 'BEARISH'
                  ? 'bg-red-500/15 text-red-400 border-red-500/20'
                  : 'bg-slate-500/15 text-slate-400 border-slate-500/20'
              }`}>
              {analysis.primary_trend || 'Unknown'}
            </span>
            <span className="text-xs text-slate-500 font-mono-num">
              {analysis.trend_strength?.toFixed(0) || 0}% strength
            </span>
          </div>
        </div>

        {/* Signal */}
        <SignalDisplay signal={analysis.signal} conviction={analysis.conviction} />

        {/* Stage */}
        <div className="card">
          <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
            Weinstein Stage
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            Stage {analysis.weinstein_stage || 'N/A'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {analysis.stage_description || 'Unknown'}
          </div>
        </div>
      </div>

      {/* Composite Score */}
      {analysis.scores && (
        <div className="animate-fade-in-up" style={{ animationDelay: '150ms' }}>
          <ScoreCard scores={analysis.scores} />
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 animate-fade-in-up" style={{ animationDelay: '225ms' }}>
        {/* Chart */}
        <div className="card">
          <h3 className="card-header">Price Chart</h3>
          {symbol && <PriceChart symbol={symbol} />}
        </div>

        {/* Analysis Summary */}
        {analysis && <AnalysisSummary analysis={analysis} />}
      </div>

      {/* Trade Suggestion */}
      {analysis.signal && analysis.signal !== 'HOLD' && (
        <div className="animate-fade-in-up" style={{ animationDelay: '300ms' }}>
          <TradeSuggestion
            symbol={analysis.symbol}
            signal={analysis.signal}
            conviction={analysis.conviction}
            currentPrice={analysis.current_price}
          />
        </div>
      )}
    </div>
  );
}
