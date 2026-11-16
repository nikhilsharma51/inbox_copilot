
'use client';

import { ReactNode } from 'react';
import { AuthProvider } from '@/lib/auth_context';
import { ErrorBoundary } from '@/components/error_boundary';

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
