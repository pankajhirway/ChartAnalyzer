import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import { useQuery } from '@tanstack/react-query';
import { createChart, ColorType } from 'lightweight-charts';
import { stockApi } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { Annotation } from '../../types';
import { useAnnotations } from '../../hooks/useAnnotations';
import { useAnnotationStore } from '../../store/annotationStore';

interface PriceChartProps {
  symbol: string;
  timeframe?: string;
  annotations?: Annotation[];
  annotationsVisible?: boolean;
}

export interface PriceChartRef {
  exportChart: () => void;
}

export const PriceChart = forwardRef<PriceChartRef, PriceChartProps>(
  ({ symbol, timeframe = '1d', annotations = [], annotationsVisible = true }, ref) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const candlestickSeriesRef = useRef<ReturnType<typeof createChart>['addCandlestickSeries'] | null>(null);
  const volumeSeriesRef = useRef<ReturnType<typeof createChart>['addHistogramSeries'] | null>(null);
  const annotationSeriesRef = useRef<Map<number, any>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Auto-save annotations hook
  const { drawing, handleChartClick, getPreviewAnnotation } = useAnnotations({
    symbol,
    enabled: !!symbol,
  });

  // Get stopDrawing from store for escape key handling
  const stopDrawing = useAnnotationStore((state) => state.stopDrawing);

  // Expose export function via ref
  useImperativeHandle(ref, () => ({
    exportChart: () => {
      if (!chartRef.current) return;

      try {
        const dataUrl = chartRef.current.takeScreenshot().toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `${symbol}-chart-${new Date().toISOString().split('T')[0]}.png`;
        link.href = dataUrl;
        link.click();
      } catch (e) {
        console.error('Failed to export chart:', e);
      }
    },
  }));

  const { data: history, error: queryError } = useQuery({
    queryKey: ['history', symbol, timeframe],
    queryFn: () => stockApi.getHistory(symbol, timeframe, 180),
    enabled: !!symbol,
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
        height: 400,
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
      const volumeSeries = chart.addHistogramSeries({
        color: '#3b82f6',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: '',
      });

      chart.priceScale('').applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      });

      chartRef.current = chart;
      candlestickSeriesRef.current = candlestickSeries as any;
      volumeSeriesRef.current = volumeSeries as any;

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
        } catch (e) {
          // Chart already removed
        }
        chartRef.current = null;
        candlestickSeriesRef.current = null;
        volumeSeriesRef.current = null;
        annotationSeriesRef.current.clear();
      };
    } catch (e: any) {
      console.error('Chart initialization error:', e);
      setError(e.message || 'Failed to initialize chart');
    }
  }, []);

  // Update chart data when history loads
  useEffect(() => {
    if (!history || !candlestickSeriesRef.current || !volumeSeriesRef.current || !chartRef.current) {
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

      const volumeData = history.data.map((item: any) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000) as any,
        value: item.volume,
        color: item.close >= item.open
          ? 'rgba(16, 185, 129, 0.25)'
          : 'rgba(239, 68, 68, 0.25)',
      }));

      (candlestickSeriesRef.current as any).setData(candleData);
      (volumeSeriesRef.current as any).setData(volumeData);

      chartRef.current.timeScale().fitContent();
      setIsLoading(false);
      setError(null);
    } catch (e: any) {
      console.error('Chart data error:', e);
      setError(e.message || 'Failed to load chart data');
      setIsLoading(false);
    }
  }, [history]);

  // Handle query error
  useEffect(() => {
    if (queryError) {
      setError('Failed to fetch price data');
      setIsLoading(false);
    }
  }, [queryError]);

  /**
   * Handle chart click for annotation drawing
   * Converts DOM coordinates to chart time/price coordinates
   */
  const handleContainerClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!chartRef.current || !candlestickSeriesRef.current) {
      return;
    }

    const rect = chartContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    // Calculate click position relative to chart container
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Convert to chart coordinates
    const chart = chartRef.current;
    const timeScale = chart.timeScale();
    const priceScale = (candlestickSeriesRef.current as any).priceScale();

    // Get the time coordinate
    const time = timeScale.coordinateToTime(x);
    if (!time) return;

    // Get the price coordinate
    const price = priceScale.coordinateToPrice(y);
    if (price === null || price === undefined) return;

    // Convert time to seconds timestamp (handle number, string, and BusinessDay formats)
    let timeInSeconds: number;
    if (typeof time === 'number') {
      timeInSeconds = Math.floor(time);
    } else if (typeof time === 'string') {
      timeInSeconds = Math.floor(new Date(time).getTime() / 1000);
    } else {
      // BusinessDay object - has year, month, day properties
      const businessDay = time as any;
      if (businessDay.year !== undefined) {
        timeInSeconds = Math.floor(new Date(businessDay.year, businessDay.month - 1, businessDay.day).getTime() / 1000);
      } else {
        timeInSeconds = Math.floor(Date.now() / 1000);
      }
    }

    // Handle the click for annotation drawing
    handleChartClick(timeInSeconds, price);
  }, [handleChartClick]);

  /**
   * Handle Escape key to cancel drawing
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && drawing.isActive) {
        // Stop drawing
        stopDrawing();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [drawing.isActive, stopDrawing]);

  // Handle annotations - create, update, and remove line series
  useEffect(() => {
    if (!chartRef.current) return;

    const chart = chartRef.current;
    const currentSeries = annotationSeriesRef.current;
    const validAnnotationIds = new Set<number>();
    const previewId = -1; // Special ID for preview annotation

    // Get preview annotation if drawing is active
    const previewAnnotation = getPreviewAnnotation();

    try {
      // Process each annotation
      annotations.forEach((annotation) => {
        validAnnotationIds.add(annotation.id);

        // Skip if annotation is not visible globally or individually
        if (!annotation.visible || !annotationsVisible) {
          // Hide existing series if present
          const existingSeries = currentSeries.get(annotation.id);
          if (existingSeries) {
            try {
              (existingSeries as any).applyOptions({ visible: false });
            } catch (e) {
              // Series might have been removed
            }
          }
          return;
        }

        // Skip if missing coordinates
        if (annotation.x1 === undefined || annotation.y1 === undefined) {
          return;
        }

        // Check if series already exists
        const existingSeries = currentSeries.get(annotation.id);

        if (existingSeries) {
          // Update existing series and make it visible
          updateLineSeries(existingSeries, annotation);
        } else {
          // Create new line series
          const newSeries = createAnnotationLineSeries(chart, annotation);
          if (newSeries) {
            currentSeries.set(annotation.id, newSeries);
          }
        }
      });

      // Process preview annotation if drawing
      if (previewAnnotation && previewAnnotation.x1 !== undefined && previewAnnotation.y1 !== undefined) {
        const previewSeries = currentSeries.get(previewId);
        const previewAnnotationData = {
          id: previewId,
          symbol,
          annotation_type: previewAnnotation.annotation_type || 'TRENDLINE',
          x1: previewAnnotation.x1,
          y1: previewAnnotation.y1,
          x2: previewAnnotation.x2,
          y2: previewAnnotation.y2,
          color: previewAnnotation.color || '#FF0000',
          line_style: previewAnnotation.line_style || 'SOLID',
          line_width: previewAnnotation.line_width || '2',
          visible: true,
        } as Annotation;

        if (previewSeries) {
          updateLineSeries(previewSeries, previewAnnotationData);
        } else {
          const newSeries = createAnnotationLineSeries(chart, previewAnnotationData);
          if (newSeries) {
            currentSeries.set(previewId, newSeries);
          }
        }
      } else {
        // Remove preview series if not drawing
        const previewSeries = currentSeries.get(previewId);
        if (previewSeries) {
          try {
            chart.removeSeries(previewSeries);
          } catch (e) {
            // Series already removed
          }
          currentSeries.delete(previewId);
        }
      }

      // Remove series for annotations that no longer exist (except preview)
      for (const [id, series] of currentSeries) {
        if (!validAnnotationIds.has(id) && id !== previewId) {
          try {
            chart.removeSeries(series);
          } catch (e) {
            // Series already removed
          }
          currentSeries.delete(id);
        }
      }
    } catch (e: any) {
      console.error('Annotation processing error:', e);
    }
  }, [annotations, annotationsVisible, getPreviewAnnotation, drawing.isActive, symbol]);

  // Helper function to create a line series for an annotation
  function createAnnotationLineSeries(
    chart: ReturnType<typeof createChart>,
    annotation: Annotation
  ): any | null {
    try {
      // Convert line style to lightweight-charts format
      const lineStyle = getLineStyle(annotation.line_style);
      const lineWidth = parseInt(annotation.line_width, 10) as 1 | 2 | 3 | 4;

      const series = chart.addLineSeries({
        color: annotation.color,
        lineWidth,
        lineStyle,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      // Set data for the series
      const seriesData = createSeriesData(annotation);
      (series as any).setData(seriesData);

      // Apply options for title
      if (annotation.title) {
        (series as any).applyOptions({
          title: annotation.title,
        });
      }

      return series;
    } catch (e) {
      console.error('Failed to create annotation line series:', e);
      return null;
    }
  }

  // Helper function to update an existing line series
  function updateLineSeries(
    series: any,
    annotation: Annotation
  ): void {
    try {
      const lineStyle = getLineStyle(annotation.line_style);
      const lineWidth = parseInt(annotation.line_width, 10) as 1 | 2 | 3 | 4;

      (series as any).applyOptions({
        color: annotation.color,
        lineWidth,
        lineStyle,
        title: annotation.title || '',
      });

      // Update data
      const seriesData = createSeriesData(annotation);
      (series as any).setData(seriesData);
    } catch (e) {
      console.error('Failed to update annotation line series:', e);
    }
  }

  // Helper function to create series data from annotation
  function createSeriesData(annotation: Annotation): { time: number; value: number }[] {
    const data: { time: number; value: number }[] = [];

    if (annotation.x1 !== undefined && annotation.y1 !== undefined) {
      data.push({
        time: annotation.x1,
        value: annotation.y1,
      });
    }

    // For trendlines and two-point annotations
    if (annotation.annotation_type === 'TRENDLINE' &&
        annotation.x2 !== undefined && annotation.y2 !== undefined) {
      data.push({
        time: annotation.x2,
        value: annotation.y2,
      });
    }

    // For horizontal lines, extend the line
    if (annotation.annotation_type === 'HORIZONTAL_LINE' &&
        annotation.y1 !== undefined) {
      // Use x2 as the end point if available, otherwise extend
      const endTime = annotation.x2 !== undefined ? annotation.x2 : Math.floor(Date.now() / 1000);
      data.push({
        time: endTime,
        value: annotation.y1,
      });
    }

    return data;
  }

  // Helper function to convert line style string to lightweight-charts format
  function getLineStyle(style: string): 0 | 1 | 2 {
    switch (style) {
      case 'DASHED':
        return 2;
      case 'DOTTED':
        return 1;
      case 'SOLID':
      default:
        return 0;
    }
  }

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
        <div className="absolute inset-0 flex items-center justify-center bg-[#0b0f19]/60 backdrop-blur-sm z-10 min-h-[400px] rounded-lg">
          <div className="text-center">
            <LoadingSpinner />
            <p className="mt-2 text-slate-500 text-sm">Loading chart...</p>
          </div>
        </div>
      )}
      {drawing.isActive && (
        <div className="absolute top-2 left-2 z-20 bg-blue-500/20 border border-blue-500/30 px-3 py-1.5 rounded-lg text-xs text-blue-300 backdrop-blur-sm">
          Drawing: {drawing.tool} - Click to place points, Escape to cancel
        </div>
      )}
      <div
        ref={chartContainerRef}
        className="w-full min-h-[400px] cursor-crosshair"
        onClick={handleContainerClick}
      />
    </div>
  );
});

PriceChart.displayName = 'PriceChart';
