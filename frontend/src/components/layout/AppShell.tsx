import { HeaderBar } from './HeaderBar';
import { SplitLayout } from './SplitLayout';
import { Terminal } from '@/components/terminal/Terminal';
import { PortfolioPanel } from '@/components/dashboard/PortfolioPanel';
import { TradeFeed } from '@/components/dashboard/TradeFeed';
import { NewsFeed } from '@/components/dashboard/NewsFeed';

export function AppShell() {
  return (
    <div className="flex flex-col h-screen w-screen bg-base overflow-hidden">
      <HeaderBar />
      <SplitLayout
        left={<Terminal />}
        right={
          <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-[2] min-h-0 overflow-hidden">
              <PortfolioPanel />
            </div>
            <div className="flex-[2] min-h-0 overflow-hidden border-t border-border">
              <TradeFeed />
            </div>
            <div className="flex-[1] min-h-0 overflow-hidden border-t border-border">
              <NewsFeed />
            </div>
          </div>
        }
      />
    </div>
  );
}
