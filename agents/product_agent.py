import anthropic
import os
import json
from dotenv import load_dotenv
from message_bus import send_message, get_messages

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def call_llm(system_prompt, user_prompt):
    """Call Claude API and return the response text"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

def generate_product_spec(idea, task):
    """
    Use LLM to generate a full product specification.
    The spec includes personas, features, and user stories.
    """
    print("\n PRODUCT AGENT: Generating product specification...")

    system_prompt = """You are an experienced product manager. 
    Given a startup idea, create a detailed product specification.
    
    Respond ONLY with a JSON object in this exact format, nothing else:
    {
        "value_proposition": "one sentence describing what the product does and for whom",
        "personas": [
            {
                "name": "persona name",
                "role": "their job or situation",
                "pain_point": "specific problem they face"
            }
        ],
        "features": [
            {
                "name": "feature name",
                "description": "what it does",
                "priority": 1
            }
        ],
        "user_stories": [
            {
                "as_a": "type of user",
                "i_want": "action they want to take",
                "so_that": "benefit they get"
            }
        ]
    }
    
    Include exactly 2 personas, 5 features (priority 1-5), and 3 user stories."""

    user_prompt = f"""Startup idea: {idea}
    
    Specific focus: {task}
    
    Generate a complete product specification."""

    response = call_llm(system_prompt, user_prompt)

    # Clean response in case LLM adds markdown
    response = response.strip()
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    response = response.strip()
    if response.endswith("```"):
        response = response[:-3]

    spec = json.loads(response)
    print(f" PRODUCT AGENT: Spec generated successfully")
    print(f"   Value Proposition: {spec['value_proposition']}")
    return spec

def run_product_agent():
    """
    Main product agent function.
    Waits for a task from CEO, generates spec, sends it back.
    """
    print("\n" + "="*60)
    print(" PRODUCT AGENT STARTING")
    print("="*60)

    # Get messages from inbox
    messages = get_messages("product")

    if not messages:
        print(" PRODUCT AGENT: No messages found")
        return None

    # Process the task from CEO
    task_message = messages[0]
    idea = task_message["payload"]["idea"]
    task = task_message["payload"]["task"]

    print(f" PRODUCT AGENT: Received task from CEO")
    print(f"   Task: {task}")

    # Generate product spec using LLM
    spec = generate_product_spec(idea, task)

    # Send spec to Engineer Agent
    send_message(
        from_agent="product",
        to_agent="engineer",
        message_type="result",
        payload={"spec": spec},
        parent_message_id=task_message["message_id"]
    )

    # Send spec to Marketing Agent
    send_message(
        from_agent="product",
        to_agent="marketing",
        message_type="result",
        payload={"spec": spec},
        parent_message_id=task_message["message_id"]
    )

    # Send confirmation back to CEO
    send_message(
        from_agent="product",
        to_agent="ceo",
        message_type="confirmation",
        payload={
            "status": "completed",
            "message": "Product spec is ready",
            "spec": spec
        },
        parent_message_id=task_message["message_id"]
    )

    print(" PRODUCT AGENT: Sent spec to Engineer, Marketing and CEO")
    return spec