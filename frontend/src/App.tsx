import { AppShell } from '@/components/layout/AppShell';
import { OnboardingShell } from '@/components/onboarding/OnboardingShell';
import { NotificationLayer } from '@/components/notifications/NotificationLayer';
import { AuthPage } from '@/components/auth/AuthPage';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useInitData } from '@/hooks/useInitData';
import { useAuthStore } from '@/stores/authStore';

function AuthenticatedApp() {
  useWebSocket();
  useInitData();
  const user = useAuthStore((s) => s.user);

  return (
    <>
      <NotificationLayer />
      {user?.onboarding_completed ? <AppShell /> : <OnboardingShell />}
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
