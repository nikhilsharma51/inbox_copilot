// API Types and Data Models

export type ThreadStatus = 'new' | 'classified' | 'needs_review' | 'failed';
export type DraftStatus = 'draft' | 'sending' | 'sent' | 'discarded';

export interface User {
  id: string;
  email: string;
  google_sub: string;
}

export interface Thread {
  id: string;
  gmail_thread_id: string;
  subject: string;
  sender: string;
  snippet: string;
  last_message_at: string; // ISO UTC
  category: string | null;
  summary: string | null; // up to 160 chars
  needs_reply: boolean; // parse if backend sends a string
  priority: number | null;
  confidence: number | null;
  status: ThreadStatus;
}

export interface Message {
  id: string;
  from: string;
  date: string;
  body: string; // plain text, fetched live
  is_from_me: boolean;
}

export interface Draft {
  id: string;
  thread_id: string;
  to_addr: string; // read-only in UI
  subject: string;
  body: string;
  status: DraftStatus;
  warnings: string[]; // computed by backend
  created_at: string;
  sent_at: string | null;
}

export interface SyncResult {
  new: number;
  updated: number;
}

export interface ClassifyStatus {
  running: boolean;
  classified: number;
  total: number;
}

export interface Category {
  id: string;
  name: string;
  description: string | null;
  count: number;
}

export interface ChatResponse {
  answer: string;
  tool_calls?: string[];
  draft_id?: string;
}

export class APIError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}
