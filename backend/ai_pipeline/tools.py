import re
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.db import User, Thread, Draft
from ai_pipeline.preprocess import clean_email
from ai_pipeline.prompt import _generate_tag_and_strip_lookalikes
from ai_pipeline.draft import write_draft, flag_draft, pick_recipients, DraftFailed
from ai_pipeline.config import MAX_BODY_CHARS
from app.gmail import ReconnectNeeded


def _clamp_limit(limit: int) -> int:
    return max(1, min(20, limit))


def _format_line(thread_id: str, sender: str, subject: str, category: str, needs_reply: bool) -> str:
    sender_clean = sender.replace('\n', ' ').replace('|', ' ')[:80]
    subject_clean = subject.replace('\n', ' ').replace('|', ' ')[:80]
    needs_reply_str = "yes" if needs_reply else "no"
    return f"{thread_id} | {sender_clean} | {subject_clean} | {category} | {needs_reply_str}"


def make_tools(db: Session, user: User, mail):
    user_id = user.id
    
    @tool
    def search_emails(query: str, limit: int = 10) -> str:
        "Search emails by subject, sender, or summary. Returns up to 20 results."
        try:
            limit = _clamp_limit(limit)
            
            query_escaped = query.replace('%', r'\%').replace('_', r'\_')
            
            threads = db.query(Thread).filter(
                Thread.user_id == user_id,
                (Thread.subject.like(f"%{query_escaped}%")) |
                (Thread.sender.like(f"%{query_escaped}%")) |
                (Thread.summary.like(f"%{query_escaped}%"))
            ).limit(limit).all()
            
            if not threads:
                return "No emails found matching that query"
            
            lines = []
            for t in threads:
                category = "uncategorized"
                needs_reply = t.status == "new"
                lines.append(_format_line(t.id, t.sender, t.subject, category, needs_reply))
            
            return "\n".join(lines)
        
        except Exception as e:
            return "search failed"
    
    @tool
    def list_by_category(category: str, limit: int = 10) -> str:
        "List emails by category. Returns up to 20 results."
        try:
            limit = _clamp_limit(limit)
            
            threads = db.query(Thread).filter(
                Thread.user_id == user_id
            ).limit(limit).all()
            
            if not threads:
                return "No emails found in that category"
            
            lines = []
            for t in threads:
                needs_reply = t.status == "new"
                lines.append(_format_line(t.id, t.sender, t.subject, category, needs_reply))
            
            return "\n".join(lines)
        
        except Exception as e:
            return "list by category failed"
    
    @tool
    def get_email(thread_id: str) -> str:
        "Fetch and read a specific email thread. Returns cleaned, unwrapped text."
        try:
            thread = db.query(Thread).filter(
                Thread.id == thread_id,
                Thread.user_id == user_id
            ).first()
            
            if not thread:
                return "thread not found"
            
            try:
                gmail_thread = mail.get_thread(thread.gmail_thread_id)
            except ReconnectNeeded:
                return "mailbox needs reconnecting"
            except:
                return "thread not found"
            
            if not gmail_thread:
                return "thread not found"
            
            message_lines = []
            for msg in gmail_thread.get("messages", []):
                sender = msg.get("sender", "unknown")
                date = msg.get("date", "")
                body = msg.get("body", "")
                
                cleaned_body = clean_email(body)
                
                message_lines.append(f"From: {sender}")
                message_lines.append(f"Date: {date}")
                message_lines.append(cleaned_body)
                message_lines.append("")
            
            full_text = "\n".join(message_lines)
            
            if len(full_text) > MAX_BODY_CHARS * 3:
                full_text = full_text[:MAX_BODY_CHARS * 3]
            
            tag, _ = _generate_tag_and_strip_lookalikes("")
            wrapped = f"<email_{tag}>\n{full_text}\n</email_{tag}>"
            
            return wrapped
        
        except ReconnectNeeded:
            return "mailbox needs reconnecting"
        except Exception:
            return "failed to fetch email"
    
    @tool
    def create_draft(thread_id: str, instruction: str) -> str:
        "Create a draft reply to an email. Never sends. Returns draft ID for review."
        try:
            thread = db.query(Thread).filter(
                Thread.id == thread_id,
                Thread.user_id == user_id
            ).first()
            
            if not thread:
                return "thread not found"
            
            try:
                gmail_thread = mail.get_thread(thread.gmail_thread_id)
            except ReconnectNeeded:
                return "mailbox needs reconnecting"
            except:
                return "thread not found"
            
            if not gmail_thread:
                return "thread not found"
            
            try:
                draft_out = write_draft(gmail_thread, instruction, "professional", user.email, llm=None)
            except DraftFailed:
                return "draft failed, try again"
            except:
                return "draft generation failed"
            
            flag_draft(draft_out, gmail_thread, instruction)
            
            to_addr = ", ".join(pick_recipients(gmail_thread, user.email))
            
            draft = Draft(
                user_id=user_id,
                thread_id=thread_id,
                to_addr=to_addr,
                subject=draft_out.subject,
                body=draft_out.body,
                instruction=instruction,
                status="draft"
            )
            
            db.add(draft)
            db.commit()
            db.refresh(draft)
            
            return f"Draft saved for your review (id {draft.id})"
        
        except ReconnectNeeded:
            return "mailbox needs reconnecting"
        except DraftFailed:
            return "draft failed, try again"
        except Exception:
            return "draft creation failed"
    
    return [search_emails, list_by_category, get_email, create_draft]
