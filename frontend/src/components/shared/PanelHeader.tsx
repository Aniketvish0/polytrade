import React from 'react';

interface PanelHeaderProps {
  label: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
}

export function PanelHeader({ label, icon, actions }: PanelHeaderProps) {
  return (
    <div className="flex items-center justify-between px-3 py-1.5 border-b border-border bg-panel">
      <div className="flex items-center gap-2">
        {icon && <span className="text-muted">{icon}</span>}
        <span className="text-xxs font-semibold tracking-widest uppercase text-muted">
          {label}
        </span>
      </div>
      {actions && <div className="flex items-center gap-1">{actions}</div>}
    </div>
  );
}
