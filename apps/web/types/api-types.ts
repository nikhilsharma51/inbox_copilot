export interface User {
  id: string;
  email: string;
  google_sub: string;
}

export interface Thread {
  id: string;
  thread_id: string;
  subject: string;
  sender: string;
  summary: string | null;
  status: 'new' | 'classified' | 'needs_review' | 'failed';
  created_at: string;
  updated_at: string;
  needs_reply: string;
  priority: string;
  confidence: string;
}

export interface ThreadDetail extends Thread {
  messages: Message[];
  drafts: Draft[];
}

export interface Message {
  sender: string;
  to: string;
  date: string | null;
  body: string;
  is_from_me: boolean;
}

export interface Draft {
  id: string;
  subject: string;
  body: string;
  to_addr: string;
  status: 'draft' | 'sent' | 'discarded';
  created_at: string;
  warnings: string[];
}

export interface DraftResponse {
  id: string;
  subject: string;
  body: string;
  to_addr: string;
  status: 'draft';
  warnings: string[];
  recipient_warning: string | null;
  needs_info: string[];
}

export interface DraftListItem {
  id: string;
  subject: string;
  body: string;
  to_addr: string;
  status: 'draft' | 'sent' | 'discarded';
  warnings: string[];
  created_at: string;
}

export interface SyncResult {
  inserted: number;
  updated: number;
  skipped: number;
}

export interface ClassifyStatus {
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
  tool_calls: string[];
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
