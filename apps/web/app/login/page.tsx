import Link from "next/link";

export default async function LoginPage({
    searchParams,
}: {
    searchParams:  Promise<{error?: string}> ;
}) {

    const {error} = await searchParams;

    const messages: Record<string, string> = {
        gmail_scopes:
            "Inbox Copilot needs Gmail access to work. Please try again and leave the Gmail boxes ticked.",
        access_denied: "Sign-in was cancelled. Try again.",
    };

    const errorMessage = error ? messages[error] : undefined;

    return (
        <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#F7F6F0] px-5 py-12 text-[#263B32]">
            <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-[#DCE6D9]/50 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-40 -right-32 h-96 w-96 rounded-full bg-[#EEE9DA]/70 blur-3xl" />

            <div className="relative w-full max-w-[440px]">
                <header className="mb-8 text-center">
                    <Link
                        href="/"
                        className="mb-10 inline-flex items-center gap-2.5"
                    >
                        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#354F42] text-sm font-semibold text-white">
                            I
                        </span>
                        <span className="text-lg font-semibold tracking-tight">
                            Inbox Copilot
                        </span>
                    </Link>

                    <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-[#858B80]">
                        A calmer inbox starts here
                    </p>

                    <h1 className="font-serif text-4xl leading-tight tracking-tight text-[#263B32] sm:text-5xl">
                        Your inbox,
                        <br />
                        back in control.
                    </h1>

                    <p className="mx-auto mt-4 max-w-sm text-sm leading-6 text-[#52645A]">
                        Organize your Gmail, understand conversations faster, and prepare
                        replies without losing control of what gets sent.
                    </p>
                </header>

                <section className="rounded-[22px] border border-[#E5E3D9] bg-white p-6 shadow-[0_8px_28px_rgba(38,59,50,0.06)] sm:p-8">
                    <div className="mb-6">
                        <h2 className="text-lg font-semibold text-[#263B32]">
                            Get started
                        </h2>
                        <p className="mt-1 text-sm text-[#858B80]">
                            Sign in with your Google account to continue.
                        </p>
                    </div>

                    {errorMessage && (
                        <div
                            role="alert"
                            className="mb-5 flex gap-3 rounded-xl border border-[#E8C9B9] bg-[#FAF0EA] p-4 text-sm leading-5 text-[#985B43]"
                        >
                            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-[#C8795D] text-xs font-semibold">
                                !
                            </span>
                            <p>{error}</p>
                        </div>
                    )}

                    <a
                        href="/api/auth/google/login"
                        className="group flex min-h-12 w-full items-center justify-center gap-3 rounded-xl border border-[#DCDAD0] bg-white px-4 py-3 text-sm font-semibold text-[#263B32] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#AEB9AC] hover:bg-[#F7F8F4] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#354F42] focus-visible:ring-offset-2"
                    >
                        <svg
                            viewBox="0 0 48 48"
                            className="h-[18px] w-[18px]"
                            aria-hidden="true"
                        >
                            <path
                                fill="#EA4335"
                                d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5Z"
                            />
                            <path
                                fill="#4285F4"
                                d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.75 7.18l7.73 6C44.43 37.93 46.98 31.82 46.98 24.55Z"
                            />
                            <path
                                fill="#FBBC05"
                                d="M10.53 28.59a14.4 14.4 0 0 1 0-9.18l-7.98-6.19a23.96 23.96 0 0 0 0 21.56l7.98-6.19Z"
                            />
                            <path
                                fill="#34A853"
                                d="M24 48c6.48 0 11.93-2.13 15.91-5.8l-7.73-6c-2.15 1.45-4.92 2.3-8.18 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48Z"
                            />
                        </svg>
                        Continue with Google
                        <span className="ml-auto text-[#858B80] transition-transform duration-200 group-hover:translate-x-0.5">
                            →
                        </span>
                    </a>

                    <div className="my-7 flex items-center gap-3">
                        <div className="h-px flex-1 bg-[#E5E3D9]" />
                        <span className="text-[10px] font-medium uppercase tracking-[0.16em] text-[#A0A398]">
                            Before you continue
                        </span>
                        <div className="h-px flex-1 bg-[#E5E3D9]" />
                    </div>

                    <div className="space-y-5">
                        <div>
                            <div className="mb-3 flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#DCE6D9] text-[#354F42]">
                                    <svg
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="1.7"
                                        className="h-4 w-4"
                                    >
                                        <path d="M4 5h16v14H4z" />
                                        <path d="m4 7 8 6 8-6" />
                                    </svg>
                                </span>
                                <h3 className="text-sm font-semibold text-[#263B32]">
                                    Gmail permissions
                                </h3>
                            </div>

                            <ul className="space-y-2 pl-9 text-[13px] leading-5 text-[#52645A]">
                                <li className="flex gap-2">
                                    <span className="text-[#354F42]">✓</span>
                                    Read your mail to sort and summarize it.
                                </li>
                                <li className="flex gap-2">
                                    <span className="text-[#354F42]">✓</span>
                                    Create drafts and send replies only when you press Send.
                                </li>
                            </ul>
                        </div>

                        <div className="h-px bg-[#E5E3D9]" />

                        <div>
                            <div className="mb-2 flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#EEE9DA] text-[#7A725C]">
                                    <svg
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="1.7"
                                        className="h-4 w-4"
                                    >
                                        <rect x="5" y="10" width="14" height="11" rx="2" />
                                        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                                        <path d="M12 14v3" />
                                    </svg>
                                </span>
                                <h3 className="text-sm font-semibold text-[#263B32]">
                                    Your privacy
                                </h3>
                            </div>

                            <p className="pl-9 text-[13px] leading-5 text-[#52645A]">
                                Email bodies are never stored. Excerpts are processed by Groq.
                                You can disconnect and delete your data any time in Settings.
                            </p>
                        </div>

                        <div className="rounded-xl bg-[#F7F6F0] p-4">
                            <div className="flex gap-2.5">
                                <span className="mt-0.5 text-[#858B80]">
                                    <svg
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="1.7"
                                        className="h-4 w-4"
                                    >
                                        <circle cx="12" cy="12" r="9" />
                                        <path d="M12 11v5M12 8h.01" />
                                    </svg>
                                </span>
                                <div>
                                    <p className="text-xs font-semibold text-[#52645A]">
                                        App currently in testing
                                    </p>
                                    <p className="mt-1 text-xs leading-5 text-[#858B80]">
                                        Google may show an "unverified app" warning while this app
                                        is in testing. Click Advanced, then Continue.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <footer className="mt-6 text-center">
                    <p className="text-xs text-[#858B80]">
                        Your inbox stays yours. You stay in control.
                    </p>
                    <Link
                        href="/"
                        className="mt-3 inline-block text-xs font-medium text-[#52645A] underline decoration-[#C8CEC4] underline-offset-4 transition-colors hover:text-[#263B32]"
                    >
                        Back to home
                    </Link>
                </footer>
            </div>
        </main>
    );
}
