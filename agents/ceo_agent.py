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
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

def decompose_idea(startup_idea):
    """
    LLM CALL 1: Break the startup idea into tasks for each agent.
    This is why we can't hardcode tasks - the LLM generates them
    based on whatever idea we give it.
    """
    print("\n CEO: Decomposing startup idea into tasks...")
    
    system_prompt = """You are a CEO of a startup. Given a startup idea, 
    you must create specific tasks for three team members:
    1. Product Manager - to define the product spec
    2. Engineer - to build a landing page
    3. Marketing Manager - to create marketing copy
    
    Respond ONLY with a JSON object in this exact format, nothing else:
    {
        "product_task": "specific task description for product manager",
        "engineer_task": "specific task description for engineer",
        "marketing_task": "specific task description for marketing manager"
    }"""
    
    user_prompt = f"Startup idea: {startup_idea}"
    
    response = call_llm(system_prompt, user_prompt)
    
    # Clean response in case LLM adds markdown
    response = response.strip()
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    
    tasks = json.loads(response)
    print(f" CEO: Tasks generated for all agents")
    return tasks

def review_product_spec(spec):
    """
    LLM CALL 2: Review the product agent's output.
    This is the feedback loop - CEO actually thinks about
    whether the output is good enough or needs revision.
    """
    print("\n CEO: Reviewing product spec...")
    
    system_prompt = """You are a CEO reviewing a product specification.
    Evaluate if it is specific, detailed and complete enough.
    
    Respond ONLY with a JSON object in this exact format, nothing else:
    {
        "verdict": "approved" or "revision_needed",
        "feedback": "specific feedback if revision needed, or 'looks good' if approved",
        "reasoning": "why you made this decision"
    }"""
    
    user_prompt = f"Review this product spec:\n{json.dumps(spec, indent=2)}"
    
    response = call_llm(system_prompt, user_prompt)
    
    # Clean response
    response = response.strip()
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    
    review = json.loads(response)
    print(f" CEO: Review complete - verdict: {review['verdict']}")
    return review

def run_ceo_agent(startup_idea):
    """
    Main CEO agent function.
    This orchestrates the entire system.
    """
    print("\n" + "="*60)
    print(" CEO AGENT STARTING")
    print(f" Startup Idea: {startup_idea}")
    print("="*60)
    
    # STEP 1: Decompose idea into tasks using LLM
    tasks = decompose_idea(startup_idea)
    
    # STEP 2: Send task to Product Agent
    send_message(
        from_agent="ceo",
        to_agent="product",
        message_type="task",
        payload={
            "idea": startup_idea,
            "task": tasks["product_task"]
        }
    )
    
    # STEP 3: Wait for Product Agent to respond
    # (In our system, we'll call product agent directly
    # and it will put result in CEO's inbox)
    print("\n CEO: Waiting for Product Agent...")
    
    return tasks