import logging
import random
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db import Thread, Category
from ai_pipeline.classify import classify_thread
from ai_pipeline.config import CLASSIFY_SLEEP_MIN, CLASSIFY_SLEEP_MAX

logger = logging.getLogger(__name__)


def classify_new_threads(db: Session, user, mail, limit: int = 25, sleep_fn=None):
    if sleep_fn is None:
        sleep_fn = time.sleep
    
    categories = db.query(Category).filter(Category.user_id == user.id).all()
    category_list = [(c.name, c.description) for c in categories]
    
    if not category_list:
        category_list = [
            ("Internship", "Internship opportunities"),
            ("Placement", "Placement and job offers"),
            ("Newsletter", "Newsletters and updates"),
            ("Hackathon", "Hackathon events"),
            ("Other", "Other emails")
        ]
    
    threads = db.query(Thread).filter(
        Thread.user_id == user.id,
        Thread.status == 'new'
    ).order_by(Thread.created_at.desc()).limit(limit).all()
    
    logger.info(f"Classifying {len(threads)} threads for user {user.id}")
    
    classified_count = 0
    failed_count = 0
    
    for thread in threads:
        try:
            try:
                gmail_thread = mail.get_thread(thread.gmail_thread_id)
            except:
                gmail_thread = None
            
            if not gmail_thread or 'messages' not in gmail_thread or not gmail_thread.get('messages'):
                thread.status = 'failed'
                db.commit()
                failed_count += 1
                continue
            
            first_msg = gmail_thread['messages'][0]
            body = first_msg.get('body', '')
            
            classification, tokens = classify_thread(
                thread.subject,
                thread.sender,
                body,
                category_list
            )
            
            thread.summary = classification.summary
            thread.needs_reply = str(classification.needs_reply).lower()
            thread.priority = str(classification.priority)
            thread.confidence = str(classification.confidence)
            thread.tokens = str(tokens)
            
            if classification.category == "Needs Review" or classification.confidence < 0.6:
                thread.status = 'needs_review'
            else:
                thread.status = 'classified'
            
            thread.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            classified_count += 1
            
            logger.info(f"Classified thread {thread.id}: {classification.category}")
            
            if classified_count < len(threads):
                sleep_duration = random.uniform(CLASSIFY_SLEEP_MIN, CLASSIFY_SLEEP_MAX)
                sleep_fn(sleep_duration)
        
        except Exception as e:
            logger.error(f"Error classifying thread {thread.id}: {str(e)}")
            try:
                thread.status = 'failed'
                db.commit()
                failed_count += 1
            except:
                db.rollback()
    
    logger.info(f"Classification complete: {classified_count} classified, {failed_count} failed")
