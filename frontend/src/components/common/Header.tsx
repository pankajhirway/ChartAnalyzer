import { Link, useLocation } from 'react-router-dom';
import { Activity, ScanLine } from 'lucide-react';
import { SearchBar } from './SearchBar';

export function Header() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/60 bg-[#0b0f19]/80 backdrop-blur-xl">
      {/* Gradient accent line at top */}
      <div className="h-[2px] bg-gradient-to-r from-blue-500 via-violet-500 to-blue-500 opacity-80" />

      <div className="container mx-auto px-4 sm:px-6 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center space-x-2.5 group"
          >
            <div className="relative">
              <Activity className="w-7 h-7 text-blue-400 transition-transform duration-300 group-hover:scale-110" />
              <div className="absolute inset-0 w-7 h-7 bg-blue-400/20 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <span className="text-lg font-bold tracking-tight text-slate-100">
              Chart<span className="text-blue-400">Analyzer</span>
            </span>
          </Link>

          {/* Navigation */}
          <nav className="hidden sm:flex items-center space-x-1">
            <Link
              to="/"
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive('/')
                  ? 'bg-slate-800/60 text-slate-100'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
            >
              Dashboard
            </Link>
            <Link
              to="/scanner"
              className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive('/scanner')
                  ? 'bg-slate-800/60 text-slate-100'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
            >
              <ScanLine className="w-4 h-4" />
              <span>Scanner</span>
            </Link>
          </nav>

          {/* Search */}
          <div className="w-72 lg:w-80">
            <SearchBar />
          </div>
        </div>
      </div>
    </header>
  );
}
