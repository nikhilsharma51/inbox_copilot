import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db import User, Thread

logger = logging.getLogger(__name__)


def sync_threads(db: Session, user: User, mail):
    inserted = 0
    updated = 0
    skipped = 0
    batch_count = 0
    
    threads_list = mail.list_threads()
    logger.info(f"Syncing {len(threads_list)} threads for user {user.id}")
    
    for thread_data in threads_list:
        gmail_thread_id = thread_data["thread_id"]
        
        try:
            existing = db.query(Thread).filter(
                Thread.user_id == user.id,
                Thread.gmail_thread_id == gmail_thread_id
            ).first()
            
            if not existing:
                new_thread = Thread(
                    user_id=user.id,
                    gmail_thread_id=gmail_thread_id,
                    subject=thread_data["subject"],
                    sender=thread_data["sender"],
                    summary=thread_data["snippet"],
                    status="new",
                )
                db.add(new_thread)
                inserted += 1
            elif existing.summary != thread_data["snippet"] or existing.subject != thread_data["subject"]:
                existing.subject = thread_data["subject"]
                existing.sender = thread_data["sender"]
                existing.summary = thread_data["snippet"]
                existing.status = "new"
                updated += 1
            else:
                skipped += 1
            
            batch_count += 1
            if batch_count % 25 == 0:
                db.commit()
        
        except IntegrityError:
            db.rollback()
            skipped += 1
            continue
    
    db.commit()
    
    logger.info(f"Sync complete: {inserted} inserted, {updated} updated, {skipped} skipped")
    
    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
    }
