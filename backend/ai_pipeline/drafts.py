from email.utils import getaddresses


def pick_recipients(thread,my_email) -> list[str] :
    
    messages= thread["messages"]
    
    if not messages : 
        return []
    
    email = my_email.strip().lower()
    
    latest_message = messages[-1]
    
    
    if latest_message["is_from_me"] : 
        
        original = next((msg for msg in messages if not msg["is_from_me"]) , None)
        
        if not original :
            return []
        
        header = original["to"]
        
    else:
        header = latest_message.get("reply_to") or latest_message["sender"]
        
        recipients = []
        
        set = set()
        
        for _, address in getaddresses([header])
            address = address.strip().lower()

            if address and address != my_email and address not in seen:
                recipients.append(address)
                seen.add(address)
                
        return recipients

def get_recipient_warnings(thread, recipients) -> list[str]:
    messages = thread["messages"]

    if not messages or not recipients or messages[-1]["is_from_me"]:
        return []

    latest = messages[-1]
    sender = latest["sender"].lower()
    warnings = []

    if "noreply@" in sender or "no-reply@" in sender:
        warnings.append("This sender probably does not read replies.")

    if latest.get("list_unsubscribe"):
        warnings.append(
            "This email contains a List-Unsubscribe header. "
            "The sender may not monitor replies."
        )

    return warnings