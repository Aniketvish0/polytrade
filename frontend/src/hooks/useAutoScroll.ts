import { useRef, useEffect, useCallback } from 'react';

export function useAutoScroll(deps: unknown[] = []) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isUserScrolled = useRef(false);
  const lastScrollTop = useRef(0);

  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    const { scrollTop, scrollHeight, clientHeight } = el;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    if (scrollTop < lastScrollTop.current && distanceFromBottom > 50) {
      isUserScrolled.current = true;
    }

    if (distanceFromBottom < 20) {
      isUserScrolled.current = false;
    }

    lastScrollTop.current = scrollTop;
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    if (!isUserScrolled.current && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { containerRef };
}
