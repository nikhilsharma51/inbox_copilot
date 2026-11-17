'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');

      if (!code || !state) {
        setError('missing_params');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `/api/auth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
          {
            method: 'GET',
            credentials: 'include',
          }
        );

        if (response.ok) {
          router.push('/dashboard');
        } else {
          const data = await response.json().catch(() => ({}));
          const errorDetail = data.detail || 'unknown_error';
          
          if (errorDetail.includes('scopes')) {
            router.push('/login?error=gmail_scopes');
          } else if (errorDetail.includes('state')) {
            router.push('/login?error=invalid_state');
          } else if (errorDetail.includes('token')) {
            router.push('/login?error=token_exchange_failed');
          } else {
            router.push('/login?error=access_denied');
          }
        }
      } catch (err) {
        router.push('/login?error=access_denied');
      }
    };

    handleCallback();
  }, [router, searchParams]);

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#F7F6F0]">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-[#354F42] border-t-transparent mx-auto" />
          <p className="text-sm text-[#52645A]">Signing you in...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F7F6F0]">
      <div className="text-center">
        <p className="text-sm text-[#985B43]">Redirecting...</p>
      </div>
    </main>
  );
}
