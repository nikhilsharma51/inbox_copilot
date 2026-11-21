'use client';

import React from 'react';

type AlertType = 'info' | 'error' | 'warning' | 'success';

interface AlertProps {
  type?: AlertType;
  title?: string;
  message: string;
  onDismiss?: () => void;
  className?: string;
}

const typeStyles: Record<AlertType, string> = {
  info: 'bg-forest/10 border-forest/30 text-forest',
  error: 'bg-terracotta/10 border-terracotta/30 text-terracotta',
  warning: 'bg-sage/10 border-sage/30 text-sage',
  success: 'bg-sage/10 border-sage/30 text-sage',
};

const typeIcons: Record<AlertType, string> = {
  info: 'ℹ️',
  error: '⚠️',
  warning: '⚠️',
  success: '✓',
};

export function Alert({
  type = 'info',
  title,
  message,
  onDismiss,
  className = '',
}: AlertProps) {
  const baseStyles =
    'flex items-start gap-3 border rounded-lg p-4 relative pr-10 animate-in fade-in slide-in-from-top-2';

  const combinedClassName = [baseStyles, typeStyles[type], className]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={combinedClassName} role="alert">
      <span className="text-lg mt-0.5">{typeIcons[type]}</span>
      <div className="flex-1 min-w-0">
        {title && <div className="font-semibold">{title}</div>}
        <div className={title ? 'text-sm mt-1' : 'text-sm'}>{message}</div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="absolute top-4 right-4 p-1 hover:opacity-60 transition-opacity"
          aria-label="Dismiss"
        >
          ✕
        </button>
      )}
    </div>
  );
}
