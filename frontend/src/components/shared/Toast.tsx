import { X, AlertCircle, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import type { Toast as ToastType } from '@/stores/notificationStore';
import { useNotificationStore } from '@/stores/notificationStore';

interface ToastProps {
  toast: ToastType;
}

const iconMap = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

const colorMap = {
  info: 'border-l-accent text-accent',
  success: 'border-l-approved text-approved',
  warning: 'border-l-held text-held',
  error: 'border-l-denied text-denied',
};

export function Toast({ toast }: ToastProps) {
  const removeToast = useNotificationStore((s) => s.removeToast);
  const Icon = iconMap[toast.type];

  return (
    <div
      className={`
        flex items-start gap-2 px-3 py-2
        bg-panel border border-border border-l-2
        ${colorMap[toast.type]}
        min-w-[280px] max-w-[360px]
        animate-[slideIn_0.2s_ease-out]
      `}
    >
      <Icon size={14} className="shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium text-primary">{toast.title}</div>
        {toast.message && (
          <div className="text-xxs text-secondary mt-0.5 line-clamp-2">
            {toast.message}
          </div>
        )}
      </div>
      <button
        onClick={() => removeToast(toast.id)}
        className="text-muted hover:text-primary shrink-0"
      >
        <X size={12} />
      </button>
    </div>
  );
}
