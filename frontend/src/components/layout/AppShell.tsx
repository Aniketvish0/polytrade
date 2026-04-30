import { Sidebar } from './Sidebar';
import { HeaderBar } from './HeaderBar';
import { Terminal } from '@/components/terminal/Terminal';
import { DashboardPage } from '@/components/pages/DashboardPage';
import { PipelinePage } from '@/components/pages/PipelinePage';
import { StrategiesPage } from '@/components/pages/StrategiesPage';
import { AuditPage } from '@/components/pages/AuditPage';
import { useUIStore } from '@/stores/uiStore';

const PAGE_COMPONENTS: Record<string, React.ComponentType> = {
  chat: Terminal,
  dashboard: DashboardPage,
  pipeline: PipelinePage,
  strategies: StrategiesPage,
  audit: AuditPage,
};

export function AppShell() {
  const activePage = useUIStore((s) => s.activePage);
  const PageComponent = PAGE_COMPONENTS[activePage] || Terminal;

  return (
    <div className="flex h-screen w-screen bg-base overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <HeaderBar />
        <div className="flex-1 min-h-0 overflow-hidden">
          <PageComponent />
        </div>
      </div>
    </div>
  );
}
