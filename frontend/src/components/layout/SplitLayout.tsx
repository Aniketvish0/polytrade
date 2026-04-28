import React, { useCallback, useRef, useEffect } from 'react';
import { useUIStore } from '@/stores/uiStore';

interface SplitLayoutProps {
  left: React.ReactNode;
  right: React.ReactNode;
}

export function SplitLayout({ left, right }: SplitLayoutProps) {
  const splitRatio = useUIStore((s) => s.splitRatio);
  const setSplitRatio = useUIStore((s) => s.setSplitRatio);
  const isDragging = useUIStore((s) => s.isDragging);
  const setIsDragging = useUIStore((s) => s.setIsDragging);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);
    },
    [setIsDragging]
  );

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const ratio = (e.clientX - rect.left) / rect.width;
      setSplitRatio(ratio);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, setSplitRatio, setIsDragging]);

  const leftPercent = `${splitRatio * 100}%`;
  const rightPercent = `${(1 - splitRatio) * 100}%`;

  return (
    <div
      ref={containerRef}
      className="flex flex-1 overflow-hidden"
      style={{ minHeight: 0 }}
    >
      <div
        className="h-full overflow-hidden"
        style={{ width: leftPercent }}
      >
        {left}
      </div>

      <div
        className={`
          w-[3px] shrink-0 cursor-col-resize
          bg-border hover:bg-accent/50 transition-colors
          ${isDragging ? 'bg-accent/70' : ''}
        `}
        onMouseDown={handleMouseDown}
      />

      <div
        className="h-full overflow-hidden"
        style={{ width: rightPercent }}
      >
        {right}
      </div>
    </div>
  );
}
