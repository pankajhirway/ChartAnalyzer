// Types for the Stock Chart Analyzer frontend

export type Exchange = 'NSE' | 'BSE';

export type TrendType = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

export type SignalType = 'BUY' | 'SELL' | 'HOLD' | 'AVOID';

export type ConvictionLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type HoldingPeriod = 'INTRADAY' | 'SWING' | 'POSITIONAL';

export type WeinsteinStage = 1 | 2 | 3 | 4;

export type StopLossType = 'PERCENTAGE' | 'ATR' | 'SUPPORT' | 'SWING_LOW';

export interface Stock {
  symbol: string;
  company_name: string;
  exchange: Exchange;
  sector?: string;
  industry?: string;
  market_cap?: number;
  isin?: string;
}

export interface PriceData {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adj_close?: number;
}

export interface StockQuote {
  symbol: string;
  company_name?: string;
  last_price: number;
  change: number;
  change_percent: number;
  day_high: number;
  day_low: number;
  day_open: number;
  prev_close: number;
  volume: number;
  avg_volume?: number;
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
  timestamp: string;
}

export interface Level {
  price: number;
  strength: number;
  touches: number;
  level_type: string;
  description?: string;
}

export interface PatternMatch {
  pattern_type: string;
  pattern_name: string;
  bullish: boolean;
  completion_pct: number;
  breakout_level?: number;
  target_price?: number;
  stop_loss?: number;
  confidence: number;
  description: string;
}

export interface Indicators {
  sma_10?: number;
  sma_20?: number;
  sma_50?: number;
  sma_150?: number;
  sma_200?: number;
  ema_8?: number;
  ema_21?: number;
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  rsi_14?: number;
  stoch_k?: number;
  stoch_d?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  bb_width?: number;
  atr_14?: number;
  adx_14?: number;
  plus_di?: number;
  minus_di?: number;
  volume_sma_20?: number;
  volume_sma_50?: number;
  obv?: number;
  obv_sma?: number;
  relative_strength?: number;
}

export interface StrategyScores {
  minervini_score: number;
  weinstein_score: number;
  lynch_score?: number;
  technical_score: number;
  fundamental_score: number;
  composite_score: number;
}

export interface Target {
  price: number;
  risk_reward: number;
  description?: string;
}

export interface EntryZone {
  low: number;
  high: number;
}

export interface TradeSuggestion {
  symbol: string;
  timestamp: string;
  action: SignalType;
  conviction: ConvictionLevel;
  entry_price: number;
  entry_zone: EntryZone;
  entry_trigger: string;
  stop_loss: number;
  stop_loss_type: StopLossType;
  stop_loss_pct: number;
  risk_per_share: number;
  target_1: Target;
  target_2: Target;
  target_3: Target;
  suggested_position_pct: number;
  max_position_pct: number;
  risk_reward_ratio: number;
  holding_period: HoldingPeriod;
  strategy_source: string;
  reasoning: string[];
  warnings: string[];
  market_trend?: string;
  sector_trend?: string;
}

export interface AnalysisResult {
  symbol: string;
  company_name?: string;
  timestamp: string;
  timeframe: string;
  current_price: number;
  primary_trend: TrendType;
  trend_strength: number;
  trend_notes?: string;
  weinstein_stage: WeinsteinStage;
  stage_description?: string;
  scores: StrategyScores;
  detected_patterns: PatternMatch[];
  support_levels: Level[];
  resistance_levels: Level[];
  signal: SignalType;
  conviction: ConvictionLevel;
  indicators: Indicators;
  bullish_factors: string[];
  bearish_factors: string[];
  warnings: string[];
}

export interface ScanResult {
  symbol: string;
  company_name?: string;
  current_price: number;
  composite_score: number;
  signal: SignalType;
  conviction: ConvictionLevel;
  trend: string;
  weinstein_stage: number;
  patterns: string[];
  timestamp: string;
}

export interface WatchlistItem {
  symbol: string;
  company_name?: string;
  added_at: string;
  notes?: string;
  tags: string[];
}

export interface ScanFilter {
  universe?: string;
  min_composite_score?: number;
  max_composite_score?: number;
  signal?: SignalType;
  min_conviction?: ConvictionLevel;
  trend?: TrendType;
  weinstein_stage?: number;
  max_results?: number;

  // Fundamental filters
  pe_min?: number;
  pe_max?: number;
  pb_max?: number;
  roe_min?: number;
  roce_min?: number;
  debt_to_equity_max?: number;
  eps_growth_min?: number;
  revenue_growth_min?: number;
  market_cap_min?: number;
}

export interface FundamentalData {
  symbol: string;
  pe_ratio?: number;
  pb_ratio?: number;
  roe?: number;
  roce?: number;
  debt_to_equity?: number;
  eps_growth?: number;
  revenue_growth?: number;
  updated_at?: string;
}

export interface FundamentalScore {
  score: number;
  grade: string;
  bullish_factors: string[];
  bearish_factors: string[];
  warnings: string[];
  detail_scores: {
    pe_score: number;        // Valuation (max 25)
    growth_score: number;    // Growth (max 30)
    roe_score: number;       // Profitability (max 25)
    debt_score: number;      // Financial Health (max 20)
  };
}
