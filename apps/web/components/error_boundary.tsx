
'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
    state: State = {
        hasError: false,
    };

    static getDerivedStateFromError(): State {
        return { hasError: true };
    }

    componentDidCatch(error: Error, info: ErrorInfo) {
        console.error('Application error:', error, info);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="flex min-h-screen flex-col items-center justify-center gap-4">
                    <h1 className="text-xl font-semibold">
                        Something went wrong
                    </h1>

                    <p className="text-sm text-muted-foreground">
                        An unexpected error occurred.
                    </p>

                    <button
                        onClick={() => window.location.reload()}
                        className="rounded-md bg-primary px-4 py-2 text-primary-foreground"
                    >
                        Reload application
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
