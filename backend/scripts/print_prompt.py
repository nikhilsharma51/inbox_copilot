import json
import sys
from ai_pipeline.prompt import build_prompt

if len(sys.argv) > 1:
    search_term = sys.argv[1]
else:
    search_term = "Internship"

with open('data/fixtures.json', 'r', encoding='utf-8') as f:
    fixtures = json.load(f)

threads = fixtures['threads']

target_thread = None
for thread in threads:
    if search_term.lower() in thread.get('subject', '').lower():
        target_thread = thread
        break

if not target_thread:
    print(f"No fixture found with '{search_term}' in subject")
    sys.exit(1)

subject = target_thread.get('subject', '')
messages = target_thread.get('messages', [])

if not messages:
    print("No messages in thread")
    sys.exit(1)

sender = messages[0].get('sender', 'unknown@example.com')
body = messages[0].get('body', '')

default_categories = [
    ("Internship", "Internship opportunities and offers"),
    ("Placement", "Campus placement and job offers"),
    ("Newsletter", "Newsletters, alerts, and notifications"),
    ("Hackathon", "Hackathon invitations and announcements"),
    ("Other", "Everything else")
]

prompt = build_prompt(subject, sender, body, default_categories)

print("=" * 80)
print(f"PROMPT FOR: {subject}")
print("=" * 80)
print(prompt)
