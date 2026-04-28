import { useNotificationStore } from '@/stores/notificationStore';
import { Toast } from '@/components/shared/Toast';

export function NotificationLayer() {
  const toasts = useNotificationStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-10 right-3 z-50 flex flex-col gap-1">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} />
      ))}
    </div>
  );
}
