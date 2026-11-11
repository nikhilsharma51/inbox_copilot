from email.utils import getaddresses


def pick_recipients(thread, my_email) -> list[str]:
    messages = thread.get("messages", [])
    
    if not messages:
        return []
    
    my_email_lower = my_email.strip().lower()
    latest_message = messages[-1]
    
    if latest_message.get("is_from_me"):
        header_str = latest_message.get("to", "")
    else:
        reply_to = latest_message.get("reply_to", "")
        sender = latest_message.get("sender", "")
        header_str = reply_to if reply_to else sender
    
    recipients = []
    seen = set()
    
    for _, address in getaddresses([header_str]):
        address = address.strip().lower()
        
        if address and address != my_email_lower and address not in seen:
            recipients.append(address)
            seen.add(address)
    
    return recipients


def recipient_warning(thread) -> str or None:
    messages = thread.get("messages", [])
    
    if not messages:
        return None
    
    latest_message = messages[-1]
    
    if latest_message.get("is_from_me"):
        return None
    
    sender = latest_message.get("sender", "").lower()
    
    sender_local = sender.split("@")[0] if "@" in sender else sender
    
    if sender_local.startswith("noreply") or sender_local.startswith("no-reply") or sender_local.startswith("donotreply"):
        return "this sender probably does not read replies"
    
    if latest_message.get("list_unsubscribe"):
        return "this sender probably does not read replies"
    
    return None
