
'use client';

import { ReactNode } from 'react';
import { AuthProvider } from '@/lib/auth-context';
import { ErrorBoundary } from '@/components/error-boundary';

export default function Providers({
    children,
}: {
    children: ReactNode;
}) {
    return (
        <ErrorBoundary>
            <AuthProvider>
                {children}
            </AuthProvider>
        </ErrorBoundary>
    );
}
