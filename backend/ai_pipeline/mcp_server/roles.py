from typing import Dict , Set

ROLE_TOOLS : Dict[str,Set[str]] = {
    "sync": {
        "list_threads",        
        "get_mailbox_state",   
    },
    "categorizer": {
        "list_threads",        
        "get_thread",          
    },
    "drafter": {
        "get_thread",          
        "create_draft",        
    },
    "inspector": {
        "list_threads",        
        "get_thread",          
    },
    "sender": {
        "send_draft",          
    },
}

VALID_ROLES = set(ROLE_TOOLS.keys())

def validate_role(role: str) -> bool:
    """Check if role is valid."""
    return role in VALID_ROLES

def get_tools_for_role(role: str) -> Set[str]:
    """Get tool set for a role."""
    if not validate_role(role):
        raise ValueError(f"Invalid role: {role}")
    return ROLE_TOOLS[role].copy()

def role_can_use_tool(role: str, tool: str) -> bool:
    """Check if role can use a specific tool."""
    return tool in ROLE_TOOLS.get(role, set())