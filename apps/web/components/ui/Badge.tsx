'use client';

import React from 'react';

type BadgeTone =
  | 'forest'
  | 'terracotta'
  | 'sage'
  | 'ink'
  | 'paper'
  | 'surface'
  | 'default';

interface BadgeProps {
  children: React.ReactNode;
  tone?: BadgeTone;
  className?: string;
}

const toneStyles: Record<BadgeTone, string> = {
  forest: 'bg-forest/10 text-forest border border-forest/30',
  terracotta: 'bg-terracotta/10 text-terracotta border border-terracotta/30',
  sage: 'bg-sage/10 text-sage border border-sage/30',
  ink: 'bg-ink/10 text-ink border border-ink/30',
  paper: 'bg-paper/10 text-paper border border-paper/30',
  surface: 'bg-surface/10 text-surface border border-surface/30',
  default: 'bg-surface text-ink border border-ink/20',
};

export function Badge({
  children,
  tone = 'default',
  className = '',
}: BadgeProps) {
  const baseStyles =
    'inline-flex items-center px-3 py-1 text-sm font-medium rounded-full';

  const combinedClassName = [
    baseStyles,
    toneStyles[tone],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return <span className={combinedClassName}>{children}</span>;
}
