
"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/auth_context";
import type { Thread, ThreadDetail, Draft } from "@/types/api-types";

type View = "inbox" | "drafts";
type Filter = "all" | "needs_reply" | "priority";

const MOCK_THREADS: Thread[] = [
    {
        id: "thread-1",
        thread_id: "gmail-1",
        subject: "Re: Q4 product launch timeline",
        sender: "Alex Morgan",
        summary: "Could you review the revised launch timeline before Friday's planning meeting?",
        status: "classified",
        created_at: "2026-11-19T10:42:00Z",
        updated_at: "2026-11-19T10:42:00Z",
        needs_reply: "true",
        priority: "high",
        confidence: "0.96",
    },
    {
        id: "thread-2",
        thread_id: "gmail-2",
        subject: "October invoice — Acme",
        sender: "Acme Billing",
        summary: "Your October invoice is ready. Payment is due by the end of the month.",
        status: "classified",
        created_at: "2026-11-19T09:18:00Z",
        updated_at: "2026-11-19T09:18:00Z",
        needs_reply: "false",
        priority: "normal",
        confidence: "0.99",
    },
    {
        id: "thread-3",
        thread_id: "gmail-3",
        subject: "Following up on the proposal",
        sender: "Priya Shah",
        summary: "Wanted to check whether you had a chance to look over the proposal I sent.",
        status: "classified",
        created_at: "2026-11-18T15:30:00Z",
        updated_at: "2026-11-18T15:30:00Z",
        needs_reply: "true",
        priority: "normal",
        confidence: "0.91",
    },
    {
        id: "thread-4",
        thread_id: "gmail-4",
        subject: "Your weekly product digest",
        sender: "Product Weekly",
        summary: "This week's updates: product launches, industry news, and useful reads.",
        status: "classified",
        created_at: "2026-11-18T08:15:00Z",
        updated_at: "2026-11-18T08:15:00Z",
        needs_reply: "false",
        priority: "low",
        confidence: "0.98",
    },
    {
        id: "thread-5",
        thread_id: "gmail-5",
        subject: "Can we move tomorrow's call?",
        sender: "Jordan Lee",
        summary: "Something came up on my end. Would Thursday afternoon work instead?",
        status: "classified",
        created_at: "2026-11-17T16:05:00Z",
        updated_at: "2026-11-17T16:05:00Z",
        needs_reply: "true",
        priority: "high",
        confidence: "0.94",
    },
];

const MOCK_DETAILS: Record<string, ThreadDetail> = {
    "thread-1": {
        ...MOCK_THREADS[0],
        messages: [
            {
                sender: "Alex Morgan",
                to: "you@example.com",
                date: "2026-11-18T16:20:00Z",
                body: "Hi,\n\nI've updated the Q4 product launch timeline based on our last discussion. Could you review the revised dates before Friday's planning meeting?\n\nI'd especially appreciate your thoughts on the testing window and the proposed release date.\n\nThanks,\nAlex",
                is_from_me: false,
            },
            {
                sender: "you@example.com",
                to: "Alex Morgan",
                date: "2026-11-18T17:02:00Z",
                body: "Thanks, Alex. I'll take a look and get back to you.",
                is_from_me: true,
            },
            {
                sender: "Alex Morgan",
                to: "you@example.com",
                date: "2026-11-19T10:42:00Z",
                body: "Just sharing the updated version here as well. Let me know what you think before Friday.",
                is_from_me: false,
            },
        ],
        drafts: [
            {
                id: "draft-1",
                subject: "Re: Q4 product launch timeline",
                body: "Hi Alex,\n\nThanks for sharing the updated timeline. I've reviewed the proposed dates, and the overall plan looks good to me.\n\nI'd suggest keeping a little extra room in the testing window so we have time to address any issues before release.\n\nLet's discuss the final dates on Friday.\n\nBest",
                to_addr: "alex@example.com",
                status: "draft",
                created_at: "2026-11-19T10:50:00Z",
                warnings: [],
            },
        ],
    },
    "thread-2": {
        ...MOCK_THREADS[1],
        messages: [
            {
                sender: "Acme Billing",
                to: "you@example.com",
                date: "2026-11-19T09:18:00Z",
                body: "Hello,\n\nYour October invoice is now available. The payment deadline is November 30.\n\nThank you,\nAcme Billing",
                is_from_me: false,
            },
        ],
        drafts: [],
    },
    "thread-3": {
        ...MOCK_THREADS[2],
        messages: [
            {
                sender: "Priya Shah",
                to: "you@example.com",
                date: "2026-11-18T15:30:00Z",
                body: "Hi,\n\nJust wanted to follow up on the proposal I sent earlier this week. Have you had a chance to review it?\n\nHappy to answer any questions.\n\nPriya",
                is_from_me: false,
            },
        ],
        drafts: [],
    },
    "thread-4": {
        ...MOCK_THREADS[3],
        messages: [
            {
                sender: "Product Weekly",
                to: "you@example.com",
                date: "2026-11-18T08:15:00Z",
                body: "Here are this week's product updates, launches, and industry reads.\n\n1. New product releases\n2. Design and engineering highlights\n3. Industry news and analysis\n\nEnjoy this week's edition.",
                is_from_me: false,
            },
        ],
        drafts: [],
    },
    "thread-5": {
        ...MOCK_THREADS[4],
        messages: [
            {
                sender: "Jordan Lee",
                to: "you@example.com",
                date: "2026-11-17T16:05:00Z",
                body: "Hey,\n\nSomething came up on my end and I won't be able to make tomorrow's call.\n\nWould Thursday afternoon work for you instead?\n\nThanks,\nJordan",
                is_from_me: false,
            },
        ],
        drafts: [],
    },
};

function needsReply(value: string) {
    return ["true", "yes", "1", "needs_reply"].includes(
        value.trim().toLowerCase()
    );
}

function priorityLabel(value: string) {
    const normalized = value.trim().toLowerCase();
    if (["high", "urgent", "critical"].includes(normalized)) return "High priority";
    if (["medium", "normal"].includes(normalized)) return "Normal";
    if (["low"].includes(normalized)) return "Low priority";
    return value || "Unclassified";
}

function formatDate(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";

    const now = new Date();
    const sameDay = date.toDateString() === now.toDateString();

    if (sameDay) {
        return date.toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
        });
    }

    return date.toLocaleDateString([], {
        month: "short",
        day: "numeric",
    });
}

function initials(value: string) {
    return value
        .split(/[\s@.]+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0].toUpperCase())
        .join("");
}

export default function DashboardPage() {
    const { user, isLoading, logout } = useAuth();

    const [view, setView] = useState<View>("inbox");
    const [filter, setFilter] = useState<Filter>("all");
    const [search, setSearch] = useState("");
    const [selectedId, setSelectedId] = useState(MOCK_THREADS[0].id);
    const [draftsByThread, setDraftsByThread] = useState<Record<string, Draft[]>>(
        () =>
            Object.fromEntries(
                Object.entries(MOCK_DETAILS).map(([id, detail]) => [id, detail.drafts])
            )
    );
    const [draftBody, setDraftBody] = useState("");
    const [editingDraft, setEditingDraft] = useState(false);
    const [savedMessage, setSavedMessage] = useState("");

    const selectedThread = MOCK_THREADS.find((thread) => thread.id === selectedId);
    const selectedDetail = MOCK_DETAILS[selectedId];
    const selectedDraft = (draftsByThread[selectedId] ?? []).find(
        (draft) => draft.status === "draft"
    );

    useEffect(() => {
        setDraftBody(selectedDraft?.body ?? "");
        setEditingDraft(false);
        setSavedMessage("");
    }, [selectedId, selectedDraft?.body]);

    const filteredThreads = useMemo(() => {
        return MOCK_THREADS.filter((thread) => {
            const hasDraft = (draftsByThread[thread.id] ?? []).some(
                (draft) => draft.status === "draft"
            );

            if (view === "drafts" && !hasDraft) return false;
            if (filter === "needs_reply" && !needsReply(thread.needs_reply)) return false;
            if (
                filter === "priority" &&
                !["high", "urgent", "critical"].includes(thread.priority.toLowerCase())
            ) {
                return false;
            }

            const query = search.trim().toLowerCase();
            if (!query) return true;

            return [
                thread.sender,
                thread.subject,
                thread.summary ?? "",
            ].some((value) => value.toLowerCase().includes(query));
        });
    }, [view, filter, search, draftsByThread]);

    function saveDraft() {
        if (!selectedDraft) return;

        setDraftsByThread((current) => ({
            ...current,
            [selectedId]: (current[selectedId] ?? []).map((draft) =>
                draft.id === selectedDraft.id ? { ...draft, body: draftBody } : draft
            ),
        }));

        setEditingDraft(false);
        setSavedMessage("Draft changes saved locally");
    }

    function selectView(nextView: View) {
        setView(nextView);
        setFilter("all");
    }

    if (isLoading) {
        return <main className="grid min-h-screen place-items-center bg-[#F7F6F0] text-[#52645A]">Preparing your inbox...</main>;
    }

    const draftCount = Object.values(draftsByThread).flat().filter((d) => d.status === "draft").length;

    return (
        <main className="min-h-screen bg-[#F7F6F0] text-[#263B32] [font-family:Inter,Geist,ui-sans-serif,system-ui,sans-serif]">
            <header className="sticky top-0 z-20 flex min-h-[72px] flex-wrap items-center gap-6 border-b border-[#E5E3D9] bg-[#F7F6F0]/95 px-5 backdrop-blur md:px-8 xl:px-[max(2rem,calc((100vw-1240px)/2))]">
                <a className="flex shrink-0 items-center gap-2.5 text-lg font-semibold tracking-[-0.05em] text-[#263B32]" href="/dashboard" aria-label="Inbox Copilot home">
                    <span className="grid size-8 place-items-center rounded-lg bg-[#354F42] font-serif text-xl text-white">i.</span>
                    <span>inbox<span className="font-normal text-[#858B80]">copilot</span></span>
                </a>

                <nav className="order-3 flex h-11 w-full items-stretch gap-6 sm:order-none sm:ml-8 sm:w-auto" aria-label="Main navigation">
                    <button className={`relative px-1 text-sm transition-colors hover:text-[#263B32] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#354F42] ${view === "inbox" ? "font-semibold text-[#263B32] after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-[#354F42]" : "text-[#858B80]"}`} onClick={() => selectView("inbox")}>Inbox</button>
                    <button className={`relative flex items-center gap-2 px-1 text-sm transition-colors hover:text-[#263B32] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#354F42] ${view === "drafts" ? "font-semibold text-[#263B32] after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-[#354F42]" : "text-[#858B80]"}`} onClick={() => selectView("drafts")}>
                        Drafts <span className="rounded-full bg-[#F0EFE8] px-2 py-0.5 text-xs text-[#52645A]">{draftCount}</span>
                    </button>
                </nav>

                <div className="ml-auto flex min-w-0 items-center gap-3 text-sm">
                    <span className="hidden max-w-[220px] truncate text-[#858B80] md:inline">{user?.email ?? "Your account"}</span>
                    <button className="rounded-lg border border-[#E5E3D9] bg-white px-3 py-2 text-sm text-[#52645A] transition-colors hover:bg-[#F0EFE8] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#354F42]" onClick={() => void logout()}>Sign out</button>
                </div>
            </header>

            <section className="mx-auto max-w-[1240px] px-5 pb-8 pt-10 md:px-8 md:pt-14">
                <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
                    <div>
                        <p className="mb-3 text-xs font-semibold tracking-[0.12em] text-[#858B80]">YOUR PERSONAL INBOX</p>
                        <h1 className="font-serif text-4xl leading-[1.05] tracking-[-0.035em] text-[#263B32] sm:text-5xl">{view === "inbox" ? "A little more order." : "Your drafts."}</h1>
                        <p className="mt-3 max-w-xl text-[15px] leading-7 text-[#52645A]">{view === "inbox" ? "The important conversations, without the noise." : "Responses prepared for you. Review before anything gets sent."}</p>
                    </div>
                    <div className="inline-flex items-center gap-2 self-start rounded-full border border-[#E5E3D9] bg-white/70 px-3 py-2 text-xs text-[#52645A] sm:self-auto">
                        <span className="size-2 rounded-full bg-[#C8795D]" />
                        Sample inbox · demo data
                    </div>
                </div>

                <section className="mb-7 flex flex-col gap-3 rounded-2xl border border-[#E5E3D9] bg-[#F0EFE8] px-5 py-4 sm:flex-row sm:items-center sm:justify-between" aria-label="How Inbox Copilot works">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[#263B32]"><span className="text-lg text-[#C8795D]">✳</span> Behind the inbox</div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-[#52645A]">
                        <span>Mail received</span><span className="text-[#858B80]">→</span><span>Context sorted</span><span className="text-[#858B80]">→</span><span>Replies prepared</span>
                    </div>
                    <span className="text-xs text-[#858B80]">You stay in control</span>
                </section>

                <section className="grid min-h-[680px] overflow-hidden rounded-2xl border border-[#E5E3D9] bg-white shadow-[0_8px_28px_rgba(38,59,50,0.04)] lg:grid-cols-[minmax(310px,0.82fr)_minmax(0,1.6fr)]">
                    <aside className="flex min-h-[420px] flex-col border-b border-[#E5E3D9] lg:border-b-0 lg:border-r">
                        <div className="flex items-end justify-between px-5 pb-4 pt-6 md:px-6">
                            <div>
                                <p className="mb-1.5 text-[11px] font-semibold tracking-[0.1em] text-[#858B80]">{view === "inbox" ? "YOUR MAIL" : "PREPARED RESPONSES"}</p>
                                <h2 className="font-serif text-2xl tracking-[-0.02em]">{view === "inbox" ? "Conversations" : "Draft queue"}</h2>
                            </div>
                            <span className="rounded-full bg-[#F0EFE8] px-2.5 py-1 text-xs tabular-nums text-[#52645A]">{filteredThreads.length}</span>
                        </div>

                        <label className="mx-5 flex h-11 items-center gap-2 rounded-lg border border-[#E5E3D9] bg-white px-3 text-[#858B80] transition focus-within:border-[#354F42] focus-within:ring-2 focus-within:ring-[#DCE6D9] md:mx-6">
                            <span aria-hidden="true" className="text-xl">⌕</span>
                            <input className="min-w-0 flex-1 bg-transparent text-sm text-[#263B32] outline-none placeholder:text-[#858B80]" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search conversations" aria-label="Search conversations" />
                            {search && <button className="text-lg text-[#858B80] hover:text-[#263B32]" onClick={() => setSearch("")} aria-label="Clear search">×</button>}
                        </label>

                        <div className="flex gap-1 overflow-x-auto px-5 py-4 md:px-6">
                            {(["all", "needs_reply", "priority"] as Filter[]).map((item) => (
                                <button key={item} className={`shrink-0 rounded-lg px-3 py-2 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#354F42] ${filter === item ? "bg-[#DCE6D9] text-[#263B32]" : "text-[#52645A] hover:bg-[#F0EFE8]"}`} onClick={() => setFilter(item)}>
                                    {item === "all" ? "All" : item === "needs_reply" ? "Needs reply" : "Priority"}
                                </button>
                            ))}
                        </div>

                        <div className="flex-1">
                            {filteredThreads.map((thread) => {
                                const hasDraft = (draftsByThread[thread.id] ?? []).some((draft) => draft.status === "draft");
                                const isSelected = thread.id === selectedId;
                                const isHighPriority = ["high", "urgent", "critical"].includes(thread.priority.toLowerCase());
                                return (
                                    <button key={thread.id} className={`block w-full border-t border-[#E5E3D9] border-l-[3px] px-5 py-4 text-left transition-colors hover:bg-[#F7F6F0] focus-visible:relative focus-visible:outline-2 focus-visible:outline-[#354F42] md:px-6 ${isSelected ? "border-l-[#354F42] bg-[#F7F6F0]" : "border-l-transparent bg-white"}`} onClick={() => setSelectedId(thread.id)}>
                                        <div className="mb-1.5 flex items-start justify-between gap-3">
                                            <span className={`min-w-0 truncate text-sm ${needsReply(thread.needs_reply) ? "font-semibold text-[#263B32]" : "font-medium text-[#52645A]"}`}>{thread.sender}</span>
                                            <span className="shrink-0 pt-0.5 text-[11px] text-[#858B80]">{formatDate(thread.created_at)}</span>
                                        </div>
                                        <div className="mb-1 truncate text-[13px] font-medium text-[#263B32]">{thread.subject}</div>
                                        <div className="mb-3">
                                            <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#858B80]">AI summary</span>
                                            <p className="mt-1 line-clamp-2 text-xs leading-5 text-[#52645A]">{thread.summary}</p>
                                        </div>
                                        <div className="flex flex-wrap gap-1.5">
                                            {needsReply(thread.needs_reply) && <span className="rounded-md bg-[#EEE9DA] px-2 py-1 text-[10px] font-medium text-[#765A36]">Needs reply</span>}
                                            {hasDraft && <span className="rounded-md bg-[#DCE6D9] px-2 py-1 text-[10px] font-medium text-[#354F42]">Draft ready</span>}
                                            {isHighPriority && <span className="rounded-md bg-[#F5E6DF] px-2 py-1 text-[10px] font-medium text-[#A45E45]">Priority</span>}
                                        </div>
                                    </button>
                                );
                            })}
                            {filteredThreads.length === 0 && <div className="px-6 py-12 text-center"><p className="font-serif text-xl text-[#263B32]">Nothing here.</p><p className="mt-1 text-sm text-[#858B80]">Try another search or filter.</p></div>}
                        </div>
                    </aside>

                    <section className="min-w-0 bg-white">
                        {selectedThread && selectedDetail ? (
                            <div className="flex h-full flex-col">
                                <div className="border-b border-[#E5E3D9] px-5 py-6 md:px-8 md:py-7">
                                    <div className="mb-3 flex items-center justify-between gap-3">
                                        <span className="text-[11px] font-semibold tracking-[0.1em] text-[#858B80]">CONVERSATION</span>
                                        <span className="text-xs text-[#858B80]">{formatDate(selectedThread.created_at)}</span>
                                    </div>
                                    <h2 className="break-words font-serif text-2xl leading-tight tracking-[-0.025em] text-[#263B32] sm:text-3xl">{selectedThread.subject}</h2>
                                    <div className="mt-5 flex items-center gap-3 text-sm text-[#52645A]">
                                        <span className="grid size-9 shrink-0 place-items-center rounded-full bg-[#DCE6D9] text-xs font-semibold text-[#354F42]">{initials(selectedThread.sender)}</span>
                                        <span className="font-medium text-[#263B32]">{selectedThread.sender}</span><span className="text-[#858B80]">·</span><span className="text-[#858B80]">to you</span>
                                    </div>
                                </div>

                                <div className="space-y-5 px-5 py-6 md:px-8 md:py-7">
                                    {selectedDetail.messages.map((message, index) => (
                                        <article key={`${selectedId}-${index}`} className={`rounded-xl px-4 py-4 md:px-5 ${message.is_from_me ? "ml-4 bg-[#F0EFE8] sm:ml-10" : "mr-4 bg-white sm:mr-10"}`}>
                                            <div className="mb-3 flex items-center justify-between gap-3">
                                                <strong className="text-xs font-semibold text-[#263B32]">{message.is_from_me ? "You" : message.sender}</strong>
                                                <span className="text-[11px] text-[#858B80]">{message.date ? formatDate(message.date) : ""}</span>
                                            </div>
                                            <div className="whitespace-pre-wrap text-sm leading-7 text-[#52645A]">{message.body}</div>
                                        </article>
                                    ))}
                                </div>

                                {selectedDraft ? (
                                    <section className="mx-5 mb-6 mt-auto rounded-xl border border-[#DCE6D9] bg-[#F7F8F4] p-5 md:mx-8 md:p-6">
                                        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                                            <div className="flex items-center gap-3">
                                                <span className="grid size-9 place-items-center rounded-lg bg-[#DCE6D9] text-lg text-[#354F42]">✳</span>
                                                <div><strong className="block text-sm font-semibold text-[#263B32]">Reply prepared</strong><span className="mt-0.5 block text-xs text-[#858B80]">AI-generated suggestion · Not sent</span></div>
                                            </div>
                                            <span className="rounded-md border border-[#E5E3D9] bg-white px-2.5 py-1 text-[10px] font-semibold tracking-[0.08em] text-[#52645A]">DRAFT</span>
                                        </div>
                                        <div className="mb-4 flex flex-wrap items-center gap-2 border-b border-[#E5E3D9] pb-3 text-xs">
                                            <span className="font-semibold tracking-wide text-[#858B80]">TO</span><strong className="text-[#263B32]">{selectedDraft.to_addr}</strong>
                                        </div>
                                        {editingDraft ? (
                                            <textarea className="min-h-48 w-full resize-y rounded-lg border border-[#E5E3D9] bg-white p-4 text-sm leading-7 text-[#263B32] outline-none transition focus:border-[#354F42] focus:ring-2 focus:ring-[#DCE6D9]" value={draftBody} onChange={(event) => setDraftBody(event.target.value)} aria-label="Edit suggested reply" />
                                        ) : (
                                            <p className="whitespace-pre-wrap text-sm leading-7 text-[#52645A]">{selectedDraft.body}</p>
                                        )}
                                        {selectedDraft.warnings.length > 0 && <div className="mt-4 rounded-lg border border-[#E8D8B9] bg-[#EEE9DA] px-3 py-2 text-xs leading-5 text-[#765A36]">Review: {selectedDraft.warnings.join(" · ")}</div>}
                                        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[#E5E3D9] pt-4">
                                            <span aria-live="polite" className="text-xs text-[#858B80]">{savedMessage || "Review and edit before sending"}</span>
                                            <div className="flex gap-2">
                                                {editingDraft ? (
                                                    <>
                                                        <button className="min-h-10 rounded-lg border border-[#E5E3D9] bg-white px-4 text-sm font-medium text-[#263B32] transition hover:bg-[#F0EFE8] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#354F42]" onClick={() => { setDraftBody(selectedDraft.body); setEditingDraft(false); }}>Cancel</button>
                                                        <button className="min-h-10 rounded-lg bg-[#354F42] px-4 text-sm font-medium text-white transition hover:-translate-y-px hover:bg-[#293F35] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#354F42]" onClick={saveDraft}>Save changes</button>
                                                    </>
                                                ) : (
                                                    <button className="min-h-10 rounded-lg border border-[#E5E3D9] bg-white px-4 text-sm font-medium text-[#263B32] transition hover:bg-[#F0EFE8] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#354F42]" onClick={() => setEditingDraft(true)}>Edit draft</button>
                                                )}
                                            </div>
                                        </div>
                                    </section>
                                ) : (
                                    <div className="mx-5 mb-6 mt-auto flex items-start gap-3 rounded-xl bg-[#F0EFE8] p-5 md:mx-8">
                                        <span className="text-xl text-[#858B80]">↳</span><div><strong className="text-sm font-semibold text-[#263B32]">No reply draft yet</strong><p className="mt-1 text-xs leading-5 text-[#52645A]">A suggested response will appear here when one is prepared.</p></div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="grid min-h-[500px] place-content-center px-6 text-center"><span className="text-2xl text-[#858B80]">←</span><h2 className="mt-3 font-serif text-2xl">Select a conversation</h2><p className="mt-2 text-sm text-[#858B80]">Choose an email to read it here.</p></div>
                        )}
                    </section>
                </section>

                <footer className="flex flex-col gap-2 px-1 pt-6 text-xs text-[#858B80] sm:flex-row sm:items-center sm:justify-between">
                    <span className="font-medium text-[#52645A]">Inbox Copilot</span><span>AI handles the sorting. You make the decisions.</span>
                </footer>
            </section>
        </main>
    );
}
