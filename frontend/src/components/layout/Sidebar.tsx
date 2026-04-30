import { MessageSquare, LayoutDashboard, GitBranch, Shield, ScrollText, LogOut } from 'lucide-react';
import { useUIStore, type AppPage } from '@/stores/uiStore';
import { useAuthStore } from '@/stores/authStore';

const NAV_ITEMS: { page: AppPage; icon: typeof MessageSquare; label: string }[] = [
  { page: 'chat', icon: MessageSquare, label: 'Chat' },
  { page: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { page: 'pipeline', icon: GitBranch, label: 'Trade Pipeline' },
  { page: 'strategies', icon: Shield, label: 'Strategies & Policies' },
  { page: 'audit', icon: ScrollText, label: 'ArmorIQ Audit' },
];

export function Sidebar() {
  const activePage = useUIStore((s) => s.activePage);
  const setActivePage = useUIStore((s) => s.setActivePage);
  const logout = useAuthStore((s) => s.logout);

  return (
    <nav className="flex flex-col items-center w-12 bg-panel border-r border-border py-2 shrink-0">
      <div className="flex flex-col items-center gap-1 flex-1">
        {NAV_ITEMS.map(({ page, icon: Icon, label }) => {
          const isActive = activePage === page;
          return (
            <button
              key={page}
              onClick={() => setActivePage(page)}
              title={label}
              className={`
                w-9 h-9 flex items-center justify-center rounded transition-colors
                ${isActive ? 'bg-accent/15 text-accent' : 'text-muted hover:text-secondary hover:bg-white/5'}
              `}
            >
              <Icon size={18} />
            </button>
          );
        })}
      </div>
      <button
        onClick={logout}
        title="Logout"
        className="w-9 h-9 flex items-center justify-center text-muted hover:text-denied transition-colors"
      >
        <LogOut size={16} />
      </button>
    </nav>
  );
}
