
"use client";

import { useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  Command,
  FileText,
  Inbox,
  LockKeyhole,
  Mail,
  Menu,
  MessageSquareText,
  MoreHorizontal,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  WandSparkles,
  X,
  Zap,
} from "lucide-react";

const emails = [
  {
    id: 1,
    initials: "AS",
    sender: "Ananya Sharma",
    email: "ananya@techstart.io",
    subject: "Interview opportunity — Frontend Intern",
    preview: "We reviewed your profile and would love to schedule...",
    category: "Internships",
    time: "10:42 AM",
    priority: "High",
    color: "#E8DCCB",
    needsReply: true,
  },
  {
    id: 2,
    initials: "MS",
    sender: "MSIT Academics",
    email: "academics@msit.in",
    subject: "Important: End semester examination schedule",
    preview: "The examination timetable for the upcoming semester...",
    category: "College",
    time: "9:18 AM",
    priority: "Medium",
    color: "#D9E4DA",
    needsReply: false,
  },
  {
    id: 3,
    initials: "G",
    sender: "GitHub",
    email: "noreply@github.com",
    subject: "Your weekly development digest",
    preview: "Here's what happened in your repositories this week...",
    category: "Updates",
    time: "Yesterday",
    priority: "Low",
    color: "#E4E1DA",
    needsReply: false,
  },
  {
    id: 4,
    initials: "RK",
    sender: "Rahul Kapoor",
    email: "rahul@buildspace.dev",
    subject: "Hackathon team — quick update",
    preview: "Hey, just checking if you're available for the...",
    category: "Hackathons",
    time: "Yesterday",
    priority: "High",
    color: "#EBD9D2",
    needsReply: true,
  },
];

const questions = [
  "Which emails need my attention?",
  "Find internship opportunities",
  "Draft a reply to Ananya",
];

const responses: Record<string, string> = {
  "Which emails need my attention?":
    "You have 2 emails that may need a reply. Ananya's interview invitation is the highest priority. Rahul's hackathon update is also awaiting your response.",
  "Find internship opportunities":
    "I found 1 potential opportunity from Ananya Sharma at TechStart. The email mentions a Frontend Intern position and requests an interview schedule.",
  "Draft a reply to Ananya":
    "I've prepared a draft expressing your interest in the Frontend Intern opportunity and asking for available interview slots. You can review and edit it before sending.",
};

export default function Home() {
  const [activeEmail, setActiveEmail] = useState(1);
  const [activeFilter, setActiveFilter] = useState("All mail");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [showAssistant, setShowAssistant] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);

  const selectedEmail = emails.find((email) => email.id === activeEmail)!;

  const filteredEmails =
    activeFilter === "All mail"
      ? emails
      : activeFilter === "Needs reply"
        ? emails.filter((email) => email.needsReply)
        : emails.filter((email) => email.category === activeFilter);

  function askAssistant(value: string) {
    if (!value.trim()) return;
    setQuestion(value);
    setAnswer(
      responses[value] ??
        "I've looked through your sample inbox. I can help organize emails, identify messages needing replies, and prepare drafts for your review."
    );
    setShowAssistant(true);
  }

  return (
    <main className="min-h-screen bg-[#F7F6F0] text-[#26372F] selection:bg-[#D8E5D7] selection:text-[#26372F]">
      <nav className="relative z-30 mx-auto flex max-w-[1380px] items-center justify-between px-6 py-6 lg:px-12">
        <a href="#" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#263B32] text-[#F7F6F0]">
            <Inbox size={19} strokeWidth={1.8} />
          </div>
          <span className="text-[21px] font-semibold tracking-[-1.1px]">
            inbox<span className="font-normal text-[#9B9D8D]">copilot</span>
          </span>
        </a>

        <div className="hidden items-center gap-9 text-[13px] font-medium text-[#777E73] md:flex">
          <a href="#product" className="transition hover:text-[#26372F]">Product</a>
          <a href="#how-it-works" className="transition hover:text-[#26372F]">How it works</a>
          <a href="#privacy" className="transition hover:text-[#26372F]">Privacy</a>
        </div>

        <div className="hidden items-center gap-5 md:flex">
          <a href="/login" className="text-[13px] font-medium text-[#58645A] hover:text-[#26372F]">
            Log in
          </a>
          <a
            href="/login"
            className="flex items-center gap-2 rounded-full bg-[#263B32] px-5 py-3 text-[13px] font-medium text-white transition hover:bg-[#385044]"
          >
            Get started <ArrowUpRight size={15} />
          </a>
        </div>

        <button
          onClick={() => setMobileMenu(!mobileMenu)}
          className="rounded-lg p-2 md:hidden"
          aria-label="Toggle navigation"
        >
          {mobileMenu ? <X size={21} /> : <Menu size={21} />}
        </button>

        {mobileMenu && (
          <div className="absolute left-0 right-0 top-full flex flex-col gap-5 border-b border-[#E4E2D8] bg-[#F7F6F0] px-6 py-7 text-sm md:hidden">
            <a href="#product" onClick={() => setMobileMenu(false)}>Product</a>
            <a href="#how-it-works" onClick={() => setMobileMenu(false)}>How it works</a>
            <a href="#privacy" onClick={() => setMobileMenu(false)}>Privacy</a>
            <a href="/login" className="font-semibold">Get started →</a>
          </div>
        )}
      </nav>

      <section className="mx-auto max-w-[1380px] px-6 pb-24 pt-14 lg:px-12 lg:pb-32 lg:pt-20">
        <div className="grid items-center gap-14 lg:grid-cols-[0.88fr_1.12fr] lg:gap-12">
          <div className="relative z-10">
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[#DCDDD1] bg-[#F1F0E8] px-3.5 py-2 text-[11px] font-medium tracking-wide text-[#657467]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#789578]" />
              A more thoughtful way to manage email
            </div>

            <h1 className="max-w-[650px] font-serif text-[58px] leading-[1.04] tracking-[-3.2px] text-[#283A30] sm:text-[70px] lg:text-[76px]">
              Your inbox has
              <br />
              <span className="italic text-[#8A987C]">a lot to say.</span>
              <br />
              We'll help you
              <br />
              make sense of it.
            </h1>

            <p className="mt-7 max-w-[420px] text-[15px] leading-[1.9] text-[#7A8075]">
              An intelligent email companion that organizes your messages,
              finds what needs attention, and helps you write better replies.
              Without taking over.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-4">
              <a
                href="/login"
                className="group flex items-center gap-3 rounded-full bg-[#263B32] px-6 py-4 text-[13px] font-medium text-white transition hover:bg-[#3A5245]"
              >
                Bring order to your inbox
                <ArrowUpRight size={16} className="transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </a>
              <a
                href="#product"
                className="flex items-center gap-2 px-3 py-3 text-[13px] font-medium text-[#657467] hover:text-[#26372F]"
              >
                See how it works <ArrowDown size={15} />
              </a>
            </div>

            <div className="mt-12 flex items-center gap-5 border-t border-[#E3E1D7] pt-6">
              <div className="flex -space-x-2">
                {["#D5BDA6", "#B5C8B5", "#D9C5BC"].map((color, index) => (
                  <div
                    key={index}
                    className="h-8 w-8 rounded-full border-2 border-[#F7F6F0]"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <p className="text-[11px] leading-5 text-[#92958B]">
                Built for people with
                <br />
                more important things to do.
              </p>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-[680px]">
            <div className="absolute -right-4 -top-8 h-44 w-44 rounded-full bg-[#E7E6D8] blur-3xl" />
            <div className="absolute -bottom-12 -left-12 h-52 w-52 rounded-full bg-[#E4E9DD] blur-3xl" />

            <div className="relative overflow-hidden rounded-[15px] border border-[#DFDED4] bg-[#FFFDF8] shadow-[0_30px_80px_-35px_rgba(39,55,44,0.22)]">
              <div className="flex h-12 items-center justify-between border-b border-[#EBE9E0] px-5">
                <div className="flex gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#D8A49A]" />
                  <span className="h-2.5 w-2.5 rounded-full bg-[#DCCB9B]" />
                  <span className="h-2.5 w-2.5 rounded-full bg-[#A9BFA6]" />
                </div>
                <span className="text-[10px] font-medium tracking-wide text-[#A1A194]">
                  INBOX COPILOT / PREVIEW
                </span>
                <MoreHorizontal size={17} className="text-[#9D9E91]" />
              </div>

              <div className="grid min-h-[425px] grid-cols-[125px_1fr] sm:grid-cols-[155px_1fr]">
                <aside className="border-r border-[#EBE9E0] bg-[#FAF9F4] p-3 sm:p-4">
                  <div className="mb-6 flex items-center gap-2 text-[12px] font-semibold">
                    <Inbox size={15} /> Mailbox
                  </div>

                  {[
                    { label: "All mail", count: "24" },
                    { label: "Needs reply", count: "02" },
                    { label: "Internships", count: "08" },
                    { label: "College", count: "05" },
                    { label: "Hackathons", count: "04" },
                    { label: "Updates", count: "07" },
                  ].map((item) => (
                    <button
                      key={item.label}
                      onClick={() => setActiveFilter(item.label)}
                      className={`mb-1 flex w-full items-center justify-between rounded-md px-2 py-2 text-left text-[10px] transition sm:text-[11px] ${
                        activeFilter === item.label
                          ? "bg-[#E9EDE4] font-semibold text-[#344A39]"
                          : "text-[#8B9085] hover:bg-[#F0EFE8]"
                      }`}
                    >
                      {item.label}
                      <span className="text-[9px] text-[#A3A496]">{item.count}</span>
                    </button>
                  ))}

                  <div className="mt-9 border-t border-[#E6E4DA] pt-4">
                    <div className="flex items-center gap-2 text-[10px] text-[#92968A]">
                      <ShieldCheck size={13} /> Protected
                    </div>
                  </div>
                </aside>

                <div className="min-w-0 p-3 sm:p-5">
                  <div className="mb-5 flex items-center justify-between gap-2">
                    <div>
                      <h3 className="text-[16px] font-semibold tracking-tight">Your inbox</h3>
                      <p className="mt-1 text-[10px] text-[#9B9C91]">A little more organized today.</p>
                    </div>
                    <button className="flex items-center gap-1.5 rounded-md border border-[#E6E4DA] px-2.5 py-2 text-[10px] text-[#6D796C]">
                      <Zap size={12} /> Sync
                    </button>
                  </div>

                  <div className="mb-4 flex items-center gap-2 rounded-md bg-[#F5F4ED] px-3 py-2.5">
                    <Search size={13} className="text-[#A2A396]" />
                    <span className="text-[10px] text-[#A2A396]">Search your emails...</span>
                    <div className="ml-auto rounded border border-[#E5E3D8] px-1.5 py-0.5 text-[9px] text-[#A2A396]">⌘ K</div>
                  </div>

                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-[10px] font-semibold text-[#687467]">{activeFilter}</span>
                    <span className="text-[9px] text-[#A6A79B]">{filteredEmails.length} messages</span>
                  </div>

                  <div className="space-y-1.5">
                    {filteredEmails.map((email) => (
                      <button
                        key={email.id}
                        onClick={() => setActiveEmail(email.id)}
                        className={`w-full rounded-lg border p-2.5 text-left transition sm:p-3 ${
                          activeEmail === email.id
                            ? "border-[#C8D2C2] bg-[#F1F4ED]"
                            : "border-transparent hover:border-[#E9E7DD] hover:bg-[#FAF9F4]"
                        }`}
                      >
                        <div className="flex items-start gap-2.5">
                          <div
                            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[9px] font-semibold text-[#526052]"
                            style={{ backgroundColor: email.color }}
                          >
                            {email.initials}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-2">
                              <span className="truncate text-[10px] font-semibold text-[#3F4D41] sm:text-[11px]">
                                {email.sender}
                              </span>
                              <span className="shrink-0 text-[9px] text-[#A0A194]">{email.time}</span>
                            </div>
                            <p className="mt-1 truncate text-[10px] font-medium text-[#596256]">
                              {email.subject}
                            </p>
                            <p className="mt-1 truncate text-[9px] text-[#A0A194]">
                              {email.preview}
                            </p>
                            <div className="mt-2 flex flex-wrap items-center gap-2">
                              <span className="rounded-sm bg-[#E9EDE4] px-1.5 py-0.5 text-[8px] text-[#697A66]">
                                {email.category}
                              </span>
                              {email.needsReply && (
                                <span className="flex items-center gap-1 text-[8px] text-[#B66F4C]">
                                  <span className="h-1 w-1 rounded-full bg-[#C87C55]" />
                                  Needs reply
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>

                  {filteredEmails.length === 0 && (
                    <p className="py-10 text-center text-[11px] text-[#92968A]">No emails in this category.</p>
                  )}
                </div>
              </div>

              <div className="border-t border-[#EAE8DF] bg-[#FBFAF5] p-3 sm:px-5 sm:py-4">
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#E6EDE3] text-[#60785E]">
                    <Sparkles size={14} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-semibold">Ask your inbox</p>
                    <p className="truncate text-[9px] text-[#A0A194]">Your emails, understood in context.</p>
                  </div>
                  <button
                    onClick={() => askAssistant("Which emails need my attention?")}
                    className="flex items-center gap-1.5 rounded-md bg-[#263B32] px-3 py-2 text-[9px] font-medium text-white transition hover:bg-[#405747]"
                  >
                    Ask <ArrowUpRight size={12} />
                  </button>
                </div>
              </div>
            </div>

            <div className="absolute -bottom-9 -left-5 hidden rounded-xl border border-[#E2E0D5] bg-[#FFFDF8] p-4 shadow-lg sm:block">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#E6EDE3] text-[#647C60]">
                  <Check size={14} />
                </div>
                <div>
                  <p className="text-[10px] font-semibold">Inbox sorted</p>
                  <p className="text-[9px] text-[#999B90]">Messages organized by context</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-[#E6E4D9] bg-[#F0EFE7] py-5">
        <div className="mx-auto flex max-w-[1380px] flex-wrap items-center justify-center gap-x-12 gap-y-3 px-6 text-[10px] font-medium uppercase tracking-[2px] text-[#96988B] lg:justify-between lg:px-12">
          <span>Less inbox clutter</span>
          <span className="hidden h-1 w-1 rounded-full bg-[#B4B6A7] sm:block" />
          <span>More thoughtful replies</span>
          <span className="hidden h-1 w-1 rounded-full bg-[#B4B6A7] sm:block" />
          <span>Human-controlled AI</span>
          <span className="hidden h-1 w-1 rounded-full bg-[#B4B6A7] sm:block" />
          <span>Built around your workflow</span>
        </div>
      </section>

      <section id="product" className="mx-auto max-w-[1380px] px-6 py-24 lg:px-12 lg:py-32">
        <div className="max-w-[600px]">
          <span className="text-[11px] font-semibold uppercase tracking-[2px] text-[#9B795F]">The actual problem</span>
          <h2 className="mt-5 font-serif text-[43px] leading-[1.13] tracking-[-1.8px] sm:text-[55px]">
            Email shouldn't feel like another full-time job.
          </h2>
          <p className="mt-5 max-w-[450px] text-[14px] leading-8 text-[#85877C]">
            Between opportunities, updates, deadlines and conversations,
            important messages get buried. Inbox Copilot brings structure
            to the noise.
          </p>
        </div>

        <div className="mt-14 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-[#E4E2D8] bg-[#FBFAF5] p-7 transition hover:-translate-y-1">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#E9EDE4] text-[#637B60]">
              <Inbox size={20} />
            </div>
            <h3 className="mt-7 text-[17px] font-semibold tracking-tight">Know what matters</h3>
            <p className="mt-3 text-[13px] leading-7 text-[#85877C]">
              Emails are classified into meaningful categories, summarized,
              and prioritized so important messages don't disappear.
            </p>
            <div className="mt-7 border-t border-[#E9E7DD] pt-4 text-[10px] font-medium text-[#87927E]">
              01 / INTELLIGENT CLASSIFICATION
            </div>
          </div>

          <div className="rounded-xl border border-[#E4E2D8] bg-[#FBFAF5] p-7 transition hover:-translate-y-1">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#F2E8DD] text-[#A16F4E]">
              <WandSparkles size={20} />
            </div>
            <h3 className="mt-7 text-[17px] font-semibold tracking-tight">Replies that sound like you</h3>
            <p className="mt-3 text-[13px] leading-7 text-[#85877C]">
              Give a simple instruction. Get a contextual draft that you
              can review, edit, and send on your own terms.
            </p>
            <div className="mt-7 border-t border-[#E9E7DD] pt-4 text-[10px] font-medium text-[#A17C61]">
              02 / CONTEXTUAL DRAFTING
            </div>
          </div>

          <div className="rounded-xl border border-[#E4E2D8] bg-[#FBFAF5] p-7 transition hover:-translate-y-1">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#E6E9E9] text-[#617B7A]">
              <MessageSquareText size={20} />
            </div>
            <h3 className="mt-7 text-[17px] font-semibold tracking-tight">Talk to your inbox</h3>
            <p className="mt-3 text-[13px] leading-7 text-[#85877C]">
              Ask questions in plain language. Find conversations,
              locate opportunities, and create drafts using an AI agent.
            </p>
            <div className="mt-7 border-t border-[#E9E7DD] pt-4 text-[10px] font-medium text-[#728B89]">
              03 / INBOX ASSISTANT
            </div>
          </div>
        </div>
      </section>

      <section className="overflow-hidden bg-[#293D32] py-24 text-[#F6F5EC] lg:py-32">
        <div className="mx-auto grid max-w-[1380px] items-center gap-16 px-6 lg:grid-cols-2 lg:px-12">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-[2px] text-[#B3C3A9]">
              A conversation, not a command line
            </span>
            <h2 className="mt-6 max-w-[520px] font-serif text-[48px] leading-[1.12] tracking-[-1.8px] sm:text-[60px]">
              Ask questions.
              <br />
              Get things done.
            </h2>
            <p className="mt-6 max-w-[420px] text-[14px] leading-8 text-[#B7C0B3]">
              No need to remember who sent what or where it went.
              Just ask. Your inbox assistant searches, understands
              and prepares the next step.
            </p>

            <div className="mt-9 flex items-center gap-3 text-[12px] text-[#CFD8C8]">
              <ShieldCheck size={17} />
              <span>Drafts are created for your review, never sent by the agent.</span>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#F8F7F0] p-5 text-[#354237] shadow-2xl sm:p-7">
            <div className="flex items-center justify-between border-b border-[#E7E5DB] pb-5">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#E6EDE3] text-[#5C7559]">
                  <Sparkles size={17} />
                </div>
                <div>
                  <p className="text-[13px] font-semibold">Inbox assistant</p>
                  <p className="text-[10px] text-[#9B9D91]">Ready to help</p>
                </div>
              </div>
              <span className="rounded-full bg-[#E9EEE5] px-3 py-1.5 text-[9px] text-[#698067]">Demo mode</span>
            </div>

            <div className="min-h-[215px] py-6">
              {!showAssistant ? (
                <div>
                  <p className="text-[11px] text-[#92968B]">Try asking something...</p>
                  <div className="mt-4 space-y-2">
                    {questions.map((item) => (
                      <button
                        key={item}
                        onClick={() => askAssistant(item)}
                        className="flex w-full items-center justify-between rounded-lg border border-[#E7E5DB] bg-white px-4 py-3 text-left text-[11px] transition hover:border-[#A8B89E] hover:bg-[#F6F7F1]"
                      >
                        {item}
                        <ArrowUpRight size={14} className="text-[#8A9B84]" />
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div>
                  <div className="ml-auto max-w-[90%] rounded-xl bg-[#E9EEE5] p-3 text-[11px] leading-6">
                    {question}
                  </div>
                  <div className="mt-5 flex gap-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#E9EDE4] text-[#647C60]">
                      <Sparkles size={14} />
                    </div>
                    <div className="text-[12px] leading-7 text-[#657063]">{answer}</div>
                  </div>
                  <button
                    onClick={() => {
                      setShowAssistant(false);
                      setQuestion("");
                      setAnswer("");
                    }}
                    className="mt-5 text-[10px] font-medium text-[#81927B] hover:text-[#344A39]"
                  >
                    Try another question →
                  </button>
                </div>
              )}
            </div>

            <form
              onSubmit={(event) => {
                event.preventDefault();
                askAssistant(question);
              }}
              className="flex items-center gap-2 rounded-lg border border-[#E4E2D8] bg-white p-2"
            >
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask anything about your inbox..."
                className="min-w-0 flex-1 bg-transparent px-2 py-2 text-[11px] outline-none placeholder:text-[#B0B1A6]"
              />
              <button type="submit" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[#293D32] text-white transition hover:bg-[#405747]" aria-label="Send question">
                <Send size={14} />
              </button>
            </form>
            <p className="mt-3 text-center text-[9px] text-[#A1A397]">
              Interactive sample · Uses illustrative email data
            </p>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-[1380px] px-6 py-24 lg:px-12 lg:py-32">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-[2px] text-[#9B795F]">A simpler routine</span>
            <h2 className="mt-5 font-serif text-[45px] tracking-[-1.7px] sm:text-[55px]">
              Three steps. Less noise.
            </h2>
          </div>
          <p className="max-w-[300px] text-[13px] leading-7 text-[#898B80]">
            Your existing email workflow, with a little more intelligence built in.
          </p>
        </div>

        <div className="mt-16 grid gap-10 md:grid-cols-3">
          {[
            {
              n: "01",
              title: "Connect Gmail",
              description: "Sign in securely and let Inbox Copilot organize your recent conversations.",
              icon: Mail,
            },
            {
              n: "02",
              title: "Let it organize",
              description: "Messages are categorized, summarized and prioritized based on their content.",
              icon: Command,
            },
            {
              n: "03",
              title: "Take action",
              description: "Ask questions, create contextual drafts, review and send when you're ready.",
              icon: ArrowUpRight,
            },
          ].map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.n} className="border-t border-[#DCDDD2] pt-6">
                <div className="flex items-center justify-between">
                  <span className="font-serif text-[30px] text-[#A5AB99]">{step.n}</span>
                  <Icon size={19} className="text-[#83947E]" />
                </div>
                <h3 className="mt-8 text-[18px] font-semibold">{step.title}</h3>
                <p className="mt-3 max-w-[300px] text-[13px] leading-7 text-[#85877C]">{step.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section id="privacy" className="border-y border-[#E5E3D9] bg-[#EFEEE6] py-24 lg:py-28">
        <div className="mx-auto grid max-w-[1380px] items-center gap-12 px-6 lg:grid-cols-[1fr_0.8fr] lg:px-12">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-[2px] text-[#9B795F]">Control stays with you</span>
            <h2 className="mt-5 max-w-[530px] font-serif text-[45px] leading-[1.15] tracking-[-1.8px] sm:text-[56px]">
              Smart assistance shouldn't mean giving up control.
            </h2>
            <p className="mt-5 max-w-[450px] text-[13px] leading-8 text-[#85877C]">
              Your inbox contains personal conversations. We designed Inbox
              Copilot with that responsibility in mind.
            </p>
          </div>

          <div className="space-y-0">
            {[
              {
                title: "Your approval, always",
                desc: "The AI agent can create drafts, but cannot send emails.",
                icon: ShieldCheck,
              },
              {
                title: "Protected credentials",
                desc: "Refresh tokens are encrypted before being stored.",
                icon: LockKeyhole,
              },
              {
                title: "Your data, your choice",
                desc: "Disconnect Gmail or delete your stored data from settings.",
                icon: X,
              },
              {
                title: "Email content is untrusted",
                desc: "Messages are treated as data, not instructions for the AI.",
                icon: CircleHelp,
              },
            ].map((item, index) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className={`flex gap-4 py-5 ${index !== 3 ? "border-b border-[#DCDDD2]" : ""}`}>
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#E1E8DE] text-[#60775D]">
                    <Icon size={17} />
                  </div>
                  <div>
                    <h3 className="text-[13px] font-semibold">{item.title}</h3>
                    <p className="mt-1.5 text-[11px] leading-6 text-[#85877C]">{item.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[1380px] px-6 py-24 lg:px-12 lg:py-32">
        <div className="relative overflow-hidden rounded-2xl bg-[#293D32] px-7 py-16 text-center text-[#F7F6F0] sm:px-12 sm:py-20">
          <div className="absolute -left-20 -top-28 h-72 w-72 rounded-full border border-white/10" />
          <div className="absolute -bottom-36 -right-20 h-80 w-80 rounded-full border border-white/10" />
          <div className="relative mx-auto max-w-[600px]">
            <span className="text-[10px] font-medium uppercase tracking-[2.5px] text-[#B9C8B1]">
              A better relationship with your inbox
            </span>
            <h2 className="mt-6 font-serif text-[43px] leading-[1.13] tracking-[-1.8px] sm:text-[57px]">
              Make room for what actually matters.
            </h2>
            <p className="mx-auto mt-5 max-w-[400px] text-[13px] leading-7 text-[#BAC4B7]">
              Less time sorting through emails. More time doing something with them.
            </p>
            <a
              href="/login"
              className="mt-9 inline-flex items-center gap-3 rounded-full bg-[#F5F3E9] px-7 py-4 text-[12px] font-semibold text-[#293D32] transition hover:bg-white"
            >
              Get started with Inbox Copilot <ArrowUpRight size={15} />
            </a>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#E5E3D9]">
        <div className="mx-auto flex max-w-[1380px] flex-col justify-between gap-7 px-6 py-8 sm:flex-row sm:items-center lg:px-12">
          <a href="#" className="flex items-center gap-2 text-[16px] font-semibold tracking-tight">
            <Inbox size={18} />
            inbox<span className="font-normal text-[#96998B]">copilot</span>
          </a>
          <p className="text-[11px] text-[#999B90]">
            A little less inbox. A little more life.
          </p>
          <div className="flex gap-6 text-[11px] text-[#85877C]">
            <a href="#product" className="hover:text-[#26372F]">Product</a>
            <a href="#privacy" className="hover:text-[#26372F]">Privacy</a>
            <a href="/login" className="hover:text-[#26372F]">Login</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
