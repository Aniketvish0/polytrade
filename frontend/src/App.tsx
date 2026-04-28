import { AppShell } from '@/components/layout/AppShell';
import { NotificationLayer } from '@/components/notifications/NotificationLayer';
import { AuthPage } from '@/components/auth/AuthPage';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/stores/authStore';

function AuthenticatedApp() {
  useWebSocket();

  return (
    <>
      <NotificationLayer />
      <AppShell />
    </>
  );
}

export default function App() {
  const token = useAuthStore((s) => s.token);

  if (!token) {
    return <AuthPage />;
  }

  return <AuthenticatedApp />;
}
