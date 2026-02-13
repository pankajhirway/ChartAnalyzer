import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Command } from 'lucide-react';
import { stockApi } from '../../services/api';

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data: results, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: () => stockApi.search(query, 5),
    enabled: query.length >= 2,
  });

  // Ctrl+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        setShowResults(false);
        inputRef.current?.blur();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Click outside to close
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (symbol: string) => {
    setQuery('');
    setShowResults(false);
    navigate(`/stock/${symbol}`);
  };

  const handleClear = () => {
    setQuery('');
    setShowResults(false);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative group">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setShowResults(true);
          }}
          onFocus={() => setShowResults(true)}
          placeholder="Search stocks..."
          className="w-full pl-10 pr-20 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 focus:bg-slate-800/80 transition-all duration-200"
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-1.5">
          {query ? (
            <button
              onClick={handleClear}
              className="p-0.5 rounded hover:bg-slate-700/50 transition-colors"
            >
              <X className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300" />
            </button>
          ) : (
            <kbd className="hidden sm:flex items-center space-x-0.5 px-1.5 py-0.5 bg-slate-700/40 border border-slate-600/30 rounded text-[10px] font-medium text-slate-500">
              <Command className="w-2.5 h-2.5" />
              <span>K</span>
            </kbd>
          )}
        </div>
      </div>

      {/* Search Results Dropdown */}
      {showResults && query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-1.5 bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-xl shadow-2xl z-50 max-h-80 overflow-y-auto animate-slide-down">
          {isLoading ? (
            <div className="p-4 text-center text-slate-500 text-sm">
              <div className="spinner w-5 h-5 mx-auto mb-2" />
              Searching...
            </div>
          ) : results && results.length > 0 ? (
            <div className="py-1">
              {results.map((result: any, i: number) => (
                <button
                  key={result.symbol}
                  onClick={() => handleSelect(result.symbol)}
                  className="w-full px-4 py-3 text-left hover:bg-slate-800/70 flex items-center justify-between transition-colors duration-150"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <div>
                    <div className="font-medium text-slate-200 text-sm">
                      {result.symbol}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {result.company_name}
                    </div>
                  </div>
                  <span className="text-[10px] font-medium text-slate-600 bg-slate-800/50 px-1.5 py-0.5 rounded">
                    {result.exchange}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-slate-500 text-sm">
              No results found
            </div>
          )}
        </div>
      )}
    </div>
  );
}
