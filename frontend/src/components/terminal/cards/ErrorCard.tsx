import type { ChatMessage } from '@/types/chat';
import { AlertOctagon } from 'lucide-react';

interface ErrorCardProps {
  message: ChatMessage;
}

export function ErrorCard({ message }: ErrorCardProps) {
  return (
    <div className="bg-denied/5 border border-denied/20 p-2 max-w-md">
      <div className="flex items-start gap-1.5">
        <AlertOctagon size={12} className="text-denied shrink-0 mt-0.5" />
        <div>
          <span className="font-mono text-xxs text-denied font-semibold">
            ERROR
          </span>
          <div className="text-xs text-primary mt-0.5">{message.content}</div>
          {message.data && (
            <div className="text-xxs text-muted mt-1 font-mono">
              {(message.data as { code?: string }).code ?? ''}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
