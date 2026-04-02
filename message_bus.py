import json
import uuid
from datetime import datetime

# This is the central "post office" of our system.
# All agents send and receive messages through here.
# It's just a dictionary where each key is an agent name
# and the value is a list of messages waiting for that agent.

message_bus = {
    "ceo": [],
    "product": [],
    "engineer": [],
    "marketing": [],
    "qa": []
}

# This list keeps a log of EVERY message ever sent
# so we can show the full conversation history in our demo
message_log = []

def send_message(from_agent, to_agent, message_type, payload, parent_message_id=None):
    """
    Send a message from one agent to another.
    Every message follows the exact schema required by the assignment.
    """
    message = {
        "message_id": str(uuid.uuid4()),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": message_type,  # task / result / revision_request / confirmation
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "parent_message_id": parent_message_id
    }
    
    # Put message in the recipient's inbox
    message_bus[to_agent].append(message)
    
    # Also log it for the demo
    message_log.append(message)
    
    print(f"\n📨 MESSAGE: {from_agent.upper()} → {to_agent.upper()} [{message_type}]")
    print(f"   ID: {message['message_id'][:8]}...")
    
    return message["message_id"]

def get_messages(agent_name):
    """
    Get all waiting messages for an agent and clear their inbox.
    """
    messages = message_bus[agent_name].copy()
    message_bus[agent_name] = []
    return messages

def print_full_log():
    """
    Print every message ever sent - needed for the demo.
    """
    print("\n" + "="*60)
    print("FULL MESSAGE LOG")
    print("="*60)
    for msg in message_log:
        print(f"\n[{msg['timestamp']}]")
        print(f"  FROM: {msg['from_agent']} → TO: {msg['to_agent']}")
        print(f"  TYPE: {msg['message_type']}")
        print(f"  PAYLOAD: {json.dumps(msg['payload'], indent=4)}")