import { AppShell } from '@/components/layout/AppShell';
import { NotificationLayer } from '@/components/notifications/NotificationLayer';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function App() {
  useWebSocket();

  return (
    <>
      <NotificationLayer />
      <AppShell />
    </>
  );
}
