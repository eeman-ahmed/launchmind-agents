from agents.ceo_agent import run_ceo_agent, review_product_spec
from agents.product_agent import run_product_agent
from agents.engineer_agent import run_engineer_agent
from agents.marketing_agent import run_marketing_agent
from message_bus import print_full_log, get_messages, send_message

# Our startup idea
STARTUP_IDEA = "A mobile app called CampusRide that helps university students find and share ride carpools to campus, splitting fuel costs automatically"

print(" LAUNCHMIND STARTING...")

# Step 1: CEO decomposes idea and sends task to Product Agent
tasks = run_ceo_agent(STARTUP_IDEA)

# Step 2: Product Agent generates spec
spec = run_product_agent()

# Step 3: CEO reviews the spec
if spec:
    ceo_messages = get_messages("ceo")
    if ceo_messages:
        review = review_product_spec(spec)
        print(f"\n CEO REVIEW: {review['verdict']}")
        print(f"   Reasoning: {review['reasoning']}")

        if review['verdict'] == 'revision_needed':
            print(f"\n CEO: Sending revision request to Product Agent...")
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

# Step 4: Engineer Agent builds landing page and pushes to GitHub
print("\n CEO: Sending spec to Engineer Agent...")
pr_url = run_engineer_agent()

# Step 5: Marketing Agent generates copy, sends email, posts to Slack
print("\n CEO: Sending spec to Marketing Agent...")
marketing_copy = run_marketing_agent(pr_url=pr_url)

# Print full message log
print_full_log()