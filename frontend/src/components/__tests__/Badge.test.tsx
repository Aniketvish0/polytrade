import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/shared/Badge';

describe('Badge', () => {
  it('renders "executed" status with correct text', () => {
    render(<Badge status="executed" />);
    expect(screen.getByText('EXECUTED')).toBeInTheDocument();
  });

  it('renders "held" status', () => {
    render(<Badge status="held" />);
    expect(screen.getByText('HELD')).toBeInTheDocument();
  });

  it('renders "denied" status', () => {
    render(<Badge status="denied" />);
    expect(screen.getByText('DENIED')).toBeInTheDocument();
  });

  it('renders "auto_approved" as AUTO', () => {
    render(<Badge status="auto_approved" />);
    expect(screen.getByText('AUTO')).toBeInTheDocument();
  });

  it('renders unknown status with fallback styling', () => {
    render(<Badge status="something_random" />);
    const badge = screen.getByText('UNKNOWN');
    expect(badge).toBeInTheDocument();
    // Fallback uses bg-muted/15 and text-muted classes
    expect(badge.className).toContain('bg-muted/15');
    expect(badge.className).toContain('text-muted');
  });

  it('accepts custom className', () => {
    render(<Badge status="executed" className="my-custom" />);
    const badge = screen.getByText('EXECUTED');
    expect(badge.className).toContain('my-custom');
  });
});
