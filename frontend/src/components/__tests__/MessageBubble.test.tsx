import { render, screen } from '@testing-library/react';
import { MessageBubble } from '@/components/terminal/MessageBubble';
import type { ChatMessage } from '@/types/chat';

// Mock child card components so we only test MessageBubble routing logic
vi.mock('@/components/terminal/cards/TradeProposalCard', () => ({
  TradeProposalCard: ({ message }: { message: ChatMessage }) => (
    <div data-testid="trade-proposal-card">{message.content}</div>
  ),
}));

vi.mock('@/components/terminal/cards/NewsCard', () => ({
  NewsCard: ({ message }: { message: ChatMessage }) => (
    <div data-testid="news-card">{message.content}</div>
  ),
}));

vi.mock('@/components/terminal/cards/ErrorCard', () => ({
  ErrorCard: ({ message }: { message: ChatMessage }) => (
    <div data-testid="error-card">{message.content}</div>
  ),
}));

// Mock formatTimestamp so we don't depend on locale
vi.mock('@/utils/format', () => ({
  formatTimestamp: () => '12:00:00',
}));

function makeMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: 'msg-1',
    role: 'agent',
    type: 'text',
    content: 'Hello world',
    timestamp: Date.now(),
    ...overrides,
  };
}

describe('MessageBubble', () => {
  it('renders text message with content', () => {
    render(<MessageBubble message={makeMessage({ content: 'Test content' })} />);
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders user role label as "YOU"', () => {
    render(<MessageBubble message={makeMessage({ role: 'user' })} />);
    expect(screen.getByText('YOU')).toBeInTheDocument();
  });

  it('renders agent role label as "AGENT"', () => {
    render(<MessageBubble message={makeMessage({ role: 'agent' })} />);
    expect(screen.getByText('AGENT')).toBeInTheDocument();
  });

  it('renders system role label as "SYS"', () => {
    render(<MessageBubble message={makeMessage({ role: 'system' })} />);
    expect(screen.getByText('SYS')).toBeInTheDocument();
  });

  it('renders error message with ErrorCard', () => {
    render(<MessageBubble message={makeMessage({ type: 'error', content: 'Oops' })} />);
    expect(screen.getByTestId('error-card')).toBeInTheDocument();
  });

  it('renders policy_confirm with POLICY label', () => {
    render(
      <MessageBubble
        message={makeMessage({ type: 'policy_confirm', content: 'Confirm this policy' })}
      />,
    );
    expect(screen.getByText('POLICY')).toBeInTheDocument();
    expect(screen.getByText('Confirm this policy')).toBeInTheDocument();
  });

  it('renders strategy_preview with STRATEGY label', () => {
    render(
      <MessageBubble
        message={makeMessage({ type: 'strategy_preview', content: 'Strategy details' })}
      />,
    );
    expect(screen.getByText('STRATEGY')).toBeInTheDocument();
    expect(screen.getByText('Strategy details')).toBeInTheDocument();
  });

  it('renders market_analysis with ANALYSIS label', () => {
    render(
      <MessageBubble
        message={makeMessage({ type: 'market_analysis', content: 'Analysis data' })}
      />,
    );
    expect(screen.getByText('ANALYSIS')).toBeInTheDocument();
    expect(screen.getByText('Analysis data')).toBeInTheDocument();
  });

  it('renders onboarding_step with clickable options', () => {
    render(
      <MessageBubble
        message={makeMessage({
          type: 'onboarding_step',
          content: 'Choose your risk level',
          data: { options: ['Conservative', 'Moderate', 'Aggressive'] },
        })}
      />,
    );
    expect(screen.getByText('Choose your risk level')).toBeInTheDocument();
    expect(screen.getByText('Conservative')).toBeInTheDocument();
    expect(screen.getByText('Moderate')).toBeInTheDocument();
    expect(screen.getByText('Aggressive')).toBeInTheDocument();
  });

  it('renders onboarding_step without options (empty array)', () => {
    render(
      <MessageBubble
        message={makeMessage({
          type: 'onboarding_step',
          content: 'All set!',
          data: { options: [] },
        })}
      />,
    );
    expect(screen.getByText('All set!')).toBeInTheDocument();
    // No option buttons rendered
    const container = screen.getByText('All set!').closest('div');
    expect(container?.querySelectorAll('[class*="cursor-pointer"]').length).toBe(0);
  });

  it('renders trade_proposal with TradeProposalCard', () => {
    render(
      <MessageBubble message={makeMessage({ type: 'trade_proposal', content: 'Trade' })} />,
    );
    expect(screen.getByTestId('trade-proposal-card')).toBeInTheDocument();
  });

  it('renders timestamp', () => {
    render(<MessageBubble message={makeMessage()} />);
    expect(screen.getByText('12:00:00')).toBeInTheDocument();
  });
});
