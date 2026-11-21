'use client';

import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeStyles = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
};

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  const baseStyles =
    'inline-block rounded-full border-forest border-t-transparent animate-spin';

  const combinedClassName = [baseStyles, sizeStyles[size], className]
    .filter(Boolean)
    .join(' ');

  return <div className={combinedClassName} aria-label="Loading" />;
}
