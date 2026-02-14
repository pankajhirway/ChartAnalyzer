import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { createChart, ColorType, IPriceLine, ISeriesApi } from 'lightweight-charts';
import { stockApi, analysisApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { PatternMatch } from '../../types';

interface CrosshairPosition {
  time: number | null;
  price: number | null;
}

interface TimeframeChartProps {
  symbol: string;
  timeframe: string;
  days?: number;
  height?: number;
  showVolume?: boolean;
  onCrosshairMove?: (timeframe: string, position: CrosshairPosition) => void;
  externalCrosshairPosition?: CrosshairPosition | null;
  showOverlays?: boolean;
}

export function TimeframeChart({
  symbol,
  timeframe,
  days = 180,
  height = 400,
  showVolume = true,
  onCrosshairMove,
  externalCrosshairPosition,
  showOverlays = true,
}: TimeframeChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const isInternalMoveRef = useRef(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Indicator series refs
  const sma20SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sma50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sma200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema8SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);

  const { data: history, error: queryError } = useQuery({
    queryKey: ['history', symbol, timeframe, days],
    queryFn: () => stockApi.getHistory(symbol, timeframe, days),
    enabled: !!symbol,
  });

  // Fetch indicators data
  const { data: indicators } = useQuery({
    queryKey: ['indicators', symbol, timeframe],
    queryFn: () => analysisApi.getIndicators(symbol, timeframe),
    enabled: !!symbol && showOverlays,
  });

  // Fetch patterns data
  const { data: patternsData } = useQuery({
    queryKey: ['patterns', symbol, timeframe],
    queryFn: () => analysisApi.getPatterns(symbol, timeframe),
    enabled: !!symbol && showOverlays,
  });

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    try {
      const container = chartContainerRef.current;

      // Dark theme chart
      const chart = createChart(container, {
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#64748b',
          fontFamily: "'Inter', sans-serif",
          fontSize: 11,
        },
        grid: {
          vertLines: { color: 'rgba(148, 163, 184, 0.04)' },
          horzLines: { color: 'rgba(148, 163, 184, 0.04)' },
        },
        width: container.clientWidth || 600,
        height,
        crosshair: {
          mode: 1,
          vertLine: {
            color: 'rgba(59, 130, 246, 0.3)',
            width: 1,
            style: 2,
            labelBackgroundColor: '#1e293b',
          },
          horzLine: {
            color: 'rgba(59, 130, 246, 0.3)',
            width: 1,
            style: 2,
            labelBackgroundColor: '#1e293b',
          },
        },
        rightPriceScale: {
          borderColor: 'rgba(148, 163, 184, 0.08)',
        },
        timeScale: {
          borderColor: 'rgba(148, 163, 184, 0.08)',
          timeVisible: true,
        },
      });

      // Candlestick series with premium colors
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      // Volume series
      const volumeSeries = showVolume ? chart.addHistogramSeries({
        color: '#3b82f6',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: '',
      }) : null;

      if (volumeSeries) {
        chart.priceScale('').applyOptions({
          scaleMargins: {
            top: 0.8,
            bottom: 0,
          },
        });
      }

      // Indicator line series
      const sma20Series = showOverlays ? chart.addLineSeries({
        color: '#3b82f6',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: true,
        title: 'SMA 20',
      }) : null;

      const sma50Series = showOverlays ? chart.addLineSeries({
        color: '#f59e0b',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: true,
        title: 'SMA 50',
      }) : null;

      const sma200Series = showOverlays ? chart.addLineSeries({
        color: '#8b5cf6',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: true,
        title: 'SMA 200',
      }) : null;

      const ema8Series = showOverlays ? chart.addLineSeries({
        color: '#06b6d4',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: true,
        title: 'EMA 8',
      }) : null;

      const ema21Series = showOverlays ? chart.addLineSeries({
        color: '#ec4899',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: true,
        title: 'EMA 21',
      }) : null;

      chartRef.current = chart;
      candlestickSeriesRef.current = candlestickSeries;
      volumeSeriesRef.current = volumeSeries;
      sma20SeriesRef.current = sma20Series;
      sma50SeriesRef.current = sma50Series;
      sma200SeriesRef.current = sma200Series;
      ema8SeriesRef.current = ema8Series;
      ema21SeriesRef.current = ema21Series;

      // Subscribe to crosshair move events for synchronization
      chart.subscribeCrosshairMove((param) => {
        if (!param.time || !param.point || isInternalMoveRef.current) {
          if (!param.time && onCrosshairMove) {
            onCrosshairMove(timeframe, { time: null, price: null });
          }
          return;
        }

        if (onCrosshairMove && !isInternalMoveRef.current) {
          let time: number;
          if (typeof param.time === 'number') {
            time = param.time;
          } else if (typeof param.time === 'string') {
            time = Math.floor(new Date(param.time).getTime() / 1000);
          } else {
            // BusinessDay type - skip synchronization
            return;
          }
          onCrosshairMove(timeframe, { time, price: param.point.y ?? null });
        }
      });

      // Handle resize
      const handleResize = () => {
        if (chartContainerRef.current && chartRef.current) {
          chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        }
      };

      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        try {
          chart.remove();
        } catch {
          // Chart already removed
        }
        chartRef.current = null;
        candlestickSeriesRef.current = null;
        volumeSeriesRef.current = null;
        sma20SeriesRef.current = null;
        sma50SeriesRef.current = null;
        sma200SeriesRef.current = null;
        ema8SeriesRef.current = null;
        ema21SeriesRef.current = null;
        priceLinesRef.current = [];
      };
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to initialize chart';
      console.error('Chart initialization error:', e);
      setError(message);
    }
  }, [height, showVolume, showOverlays, onCrosshairMove, timeframe]);

  // Update chart data when history loads
  useEffect(() => {
    if (!history || !candlestickSeriesRef.current || !chartRef.current) {
      return;
    }

    try {
      if (!history.data || history.data.length === 0) {
        setError('No historical data available');
        setIsLoading(false);
        return;
      }

      const candleData = history.data.map((item: any) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000) as any,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }));

      candlestickSeriesRef.current.setData(candleData);

      if (volumeSeriesRef.current && showVolume) {
        const volumeData = history.data.map((item: any) => ({
          time: Math.floor(new Date(item.timestamp).getTime() / 1000) as any,
          value: item.volume,
          color: item.close >= item.open
            ? 'rgba(16, 185, 129, 0.25)'
            : 'rgba(239, 68, 68, 0.25)',
        }));

        volumeSeriesRef.current.setData(volumeData);
      }

      chartRef.current.timeScale().fitContent();
      setIsLoading(false);
      setError(null);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to load chart data';
      console.error('Chart data error:', e);
      setError(message);
      setIsLoading(false);
    }
  }, [history, showVolume]);

  // Handle query error
  useEffect(() => {
    if (queryError) {
      setError('Failed to fetch price data');
      setIsLoading(false);
    }
  }, [queryError]);

  // Update indicator overlays when data is available
  useEffect(() => {
    if (!history || !history.data || !indicators || !chartRef.current) {
      return;
    }

    try {
      // Build indicator line data from history data
      const data = history.data;
      const candleData = data.map((item: any) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000) as any,
        value: item.close,
      }));

      // Helper to update indicator series
      const updateIndicatorSeries = (
        seriesRef: React.MutableRefObject<ISeriesApi<'Line'> | null>,
        value: number | undefined
      ) => {
        if (!seriesRef.current || value === undefined) return;

        // Create a horizontal line at the indicator value across all data points
        const indicatorData = candleData.map((point: any) => ({
          time: point.time,
          value: value,
        }));

        seriesRef.current.setData(indicatorData);
      };

      // Update all indicator series
      updateIndicatorSeries(sma20SeriesRef, indicators.sma_20);
      updateIndicatorSeries(sma50SeriesRef, indicators.sma_50);
      updateIndicatorSeries(sma200SeriesRef, indicators.sma_200);
      updateIndicatorSeries(ema8SeriesRef, indicators.ema_8);
      updateIndicatorSeries(ema21SeriesRef, indicators.ema_21);

    } catch (e) {
      console.error('Indicator update error:', e);
    }
  }, [history, indicators]);

  // Add pattern markers when patterns data is available
  useEffect(() => {
    if (!patternsData || !candlestickSeriesRef.current) {
      return;
    }

    try {
      const patterns = patternsData.patterns as PatternMatch[];
      if (!patterns || patterns.length === 0) {
        return;
      }

      // Clear existing price lines
      priceLinesRef.current.forEach(line => {
        try {
          candlestickSeriesRef.current?.removePriceLine(line);
        } catch {
          // Line already removed
        }
      });
      priceLinesRef.current = [];

      // Add price lines for breakout levels and support/resistance
      const newPriceLines: IPriceLine[] = [];

      patterns.forEach((pattern) => {
        if (pattern.breakout_level && candlestickSeriesRef.current) {
          const isBullish = pattern.bullish;
          const priceLine = candlestickSeriesRef.current.createPriceLine({
            price: pattern.breakout_level,
            color: isBullish ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)',
            lineWidth: 2,
            lineStyle: 2, // Dashed line
            axisLabelVisible: true,
            title: `${pattern.pattern_name} - ${pattern.completion_pct.toFixed(0)}%`,
          });

          newPriceLines.push(priceLine);
        }

        if (pattern.target_price && candlestickSeriesRef.current) {
          const priceLine = candlestickSeriesRef.current.createPriceLine({
            price: pattern.target_price,
            color: 'rgba(59, 130, 246, 0.4)',
            lineWidth: 1,
            lineStyle: 3, // Dotted line
            axisLabelVisible: true,
            title: `Target ${pattern.target_price.toFixed(2)}`,
          });

          newPriceLines.push(priceLine);
        }

        if (pattern.stop_loss && candlestickSeriesRef.current) {
          const priceLine = candlestickSeriesRef.current.createPriceLine({
            price: pattern.stop_loss,
            color: 'rgba(239, 68, 68, 0.4)',
            lineWidth: 1,
            lineStyle: 3, // Dotted line
            axisLabelVisible: true,
            title: `Stop ${pattern.stop_loss.toFixed(2)}`,
          });

          newPriceLines.push(priceLine);
        }
      });

      priceLinesRef.current = newPriceLines;
    } catch (e) {
      console.error('Pattern markers error:', e);
    }
  }, [patternsData]);

  // Sync crosshair position from external source
  useEffect(() => {
    if (!externalCrosshairPosition || !chartRef.current) {
      return;
    }

    const { time, price } = externalCrosshairPosition;
    if (time === null || price === null) {
      return;
    }

    try {
      isInternalMoveRef.current = true;
      // Try to set crosshair position if we have series
      const series = candlestickSeriesRef.current;
      if (series) {
        // Use type assertion to bypass strict type check
        (chartRef.current as any).setCrosshairPosition(
          time as any,
          price as any,
          series,
        );
      }

      // Reset flag after a short delay to ensure move completes
      setTimeout(() => {
        isInternalMoveRef.current = false;
      }, 50);
    } catch {
      // Position not available on this chart's data, ignore
      isInternalMoveRef.current = false;
    }
  }, [externalCrosshairPosition]);

  if (error) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#0b0f19]/60 backdrop-blur-sm z-10 rounded-lg" style={{ minHeight: height }}>
          <div className="text-center">
            <LoadingSpinner />
            <p className="mt-2 text-slate-500 text-sm">Loading chart...</p>
          </div>
        </div>
      )}
      <div ref={chartContainerRef} className="w-full" style={{ minHeight: height }} />
    </div>
  );
}
