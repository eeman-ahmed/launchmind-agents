from agents.ceo_agent import run_ceo_agent, review_product_spec
from agents.product_agent import run_product_agent
from message_bus import print_full_log, get_messages

# Our startup idea
STARTUP_IDEA = "A mobile app that helps university students find and share ride carpools to campus, splitting fuel costs automatically"

print(" LAUNCHMIND STARTING...")

# Step 1: CEO decomposes idea and sends task to Product Agent
tasks = run_ceo_agent(STARTUP_IDEA)

# Step 2: Product Agent runs and generates spec
spec = run_product_agent()

# Step 3: CEO reviews the spec (feedback loop)
if spec:
    ceo_messages = get_messages("ceo")
    if ceo_messages:
        review = review_product_spec(spec)
        print(f"\n CEO REVIEW: {review['verdict']}")
        print(f"   Reasoning: {review['reasoning']}")
        
        if review['verdict'] == 'revision_needed':
            print(f"\n CEO: Sending revision request to Product Agent...")
            from message_bus import send_message
            send_message(
                from_agent="ceo",
                to_agent="product",
                message_type="revision_request",
                payload={
                    "feedback": review['feedback'],
                    "original_spec": spec
                }
            )
        else:
            print("\n CEO: Product spec approved!")

# Print full message log
print_full_log()