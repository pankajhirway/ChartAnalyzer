import { useCallback, useRef, useState } from 'react';
import type { AnnotationCreate } from '../types';
import { useAnnotationStore } from '../store/annotationStore';

interface UseAnnotationsOptions {
  symbol: string;
  enabled?: boolean;
}

interface DrawingPoint {
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
}

/**
 * Hook for managing annotation drawing state and auto-save functionality.
 * Tracks the current drawing and saves annotations when completed.
 */
export function useAnnotations({
  symbol,
  enabled = true,
}: UseAnnotationsOptions) {
  const {
    drawing,
    addAnnotation,
    stopDrawing,
  } = useAnnotationStore();

  const [currentDrawing, setCurrentDrawing] = useState<DrawingPoint>({});
  const drawingStepRef = useRef(0); // 0: not started, 1: first point, 2: second point

  /**
   * Reset the current drawing state
   */
  const resetDrawing = useCallback(() => {
    setCurrentDrawing({});
    drawingStepRef.current = 0;
  }, []);

  /**
   * Handle first click - set the start point
   */
  const handleFirstPoint = useCallback((x: number, y: number) => {
    setCurrentDrawing({ x1: x, y1: y });
    drawingStepRef.current = 1;
  }, []);

  /**
   * Handle second click - set the end point and auto-save
   */
  const handleSecondPoint = useCallback(async (x: number, y: number) => {
    // Map drawing tool to annotation type (exclude SELECT)
    const toolToType: Record<string, any> = {
      'TRENDLINE': 'TRENDLINE',
      'HORIZONTAL_LINE': 'HORIZONTAL_LINE',
      'RECTANGLE': 'RECTANGLE',
      'TEXT': 'TEXT',
      'ARROW': 'ARROW',
      'FIBONACCI': 'FIBONACCI',
      'SUPPORT_RESISTANCE': 'SUPPORT_RESISTANCE',
    };

    const annotationData: AnnotationCreate = {
      symbol,
      annotation_type: toolToType[drawing.tool] || 'TRENDLINE',
      x1: currentDrawing.x1,
      y1: currentDrawing.y1,
      x2: x,
      y2: y,
      color: '#FF0000' as any,
      line_style: 'SOLID',
      line_width: '2',
    };

    // For horizontal lines, we only need y1
    if (drawing.tool === 'HORIZONTAL_LINE') {
      annotationData.x2 = undefined;
      annotationData.y2 = undefined;
    }

    await addAnnotation(annotationData);
    resetDrawing();
    stopDrawing();
  }, [symbol, drawing.tool, currentDrawing, addAnnotation, stopDrawing, resetDrawing]);

  /**
   * Handle chart click during drawing
   */
  const handleChartClick = useCallback((x: number, y: number) => {
    if (!enabled || !drawing.isActive || drawing.tool === 'SELECT') {
      return;
    }

    if (drawingStepRef.current === 0) {
      handleFirstPoint(x, y);
    } else if (drawingStepRef.current === 1) {
      handleSecondPoint(x, y);
    }
  }, [enabled, drawing.isActive, drawing.tool, handleFirstPoint, handleSecondPoint]);

  /**
   * Cancel the current drawing
   */
  const cancelDrawing = useCallback(() => {
    resetDrawing();
    stopDrawing();
  }, [resetDrawing, stopDrawing]);

  /**
   * Get the current drawing state for preview rendering
   */
  const getPreviewAnnotation = useCallback((): Partial<AnnotationCreate> | null => {
    if (drawingStepRef.current === 0 || !currentDrawing.x1 || !currentDrawing.y1) {
      return null;
    }

    // Map drawing tool to annotation type (exclude SELECT)
    const toolToType: Record<string, any> = {
      'TRENDLINE': 'TRENDLINE',
      'HORIZONTAL_LINE': 'HORIZONTAL_LINE',
      'RECTANGLE': 'RECTANGLE',
      'TEXT': 'TEXT',
      'ARROW': 'ARROW',
      'FIBONACCI': 'FIBONACCI',
      'SUPPORT_RESISTANCE': 'SUPPORT_RESISTANCE',
    };

    return {
      symbol,
      annotation_type: toolToType[drawing.tool] || 'TRENDLINE',
      x1: currentDrawing.x1,
      y1: currentDrawing.y1,
      x2: currentDrawing.x2,
      y2: currentDrawing.y2,
      color: '#FF0000',
      line_style: 'SOLID',
      line_width: '2',
    };
  }, [drawing.tool, symbol, currentDrawing]);

  return {
    drawing,
    currentDrawing,
    handleChartClick,
    cancelDrawing,
    getPreviewAnnotation,
    isDrawing: drawingStepRef.current > 0,
  };
}
