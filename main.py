from agents.ceo_agent import run_ceo_agent, review_product_spec
from agents.product_agent import run_product_agent
from agents.engineer_agent import run_engineer_agent
from agents.marketing_agent import run_marketing_agent
from agents.qa_agent import run_qa_agent
from message_bus import print_full_log, get_messages, send_message

STARTUP_IDEA = "A mobile app called CampusRide that helps university students find and share ride carpools to campus, splitting fuel costs automatically"

print(" LAUNCHMIND STARTING...")

# Step 1: CEO decomposes idea
tasks = run_ceo_agent(STARTUP_IDEA)

# Step 2: Product Agent generates spec
spec = run_product_agent()

# Step 3: CEO reviews spec — FEEDBACK LOOP 1
if spec:
    ceo_messages = get_messages("ceo")
    if ceo_messages:
        review = review_product_spec(spec)
        print(f"\n CEO REVIEW: {review['verdict']}")
        print(f"   Reasoning: {review['reasoning']}")

        if review['verdict'] == 'revision_needed':
            print(f"\n🔄 CEO: Sending revision request to Product Agent...")
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

# Step 4: Engineer Agent builds and pushes to GitHub
print("\n CEO: Sending spec to Engineer Agent...")
pr_url = run_engineer_agent()

# Step 5: Marketing Agent generates copy, sends email, posts to Slack
print("\n CEO: Sending spec to Marketing Agent...")
marketing_copy = run_marketing_agent(pr_url=pr_url)

# Step 6: CEO sends task to QA Agent
print("\n CEO: Sending review task to QA Agent...")
send_message(
    from_agent="ceo",
    to_agent="qa",
    message_type="task",
    payload={
        "pr_url": pr_url,
        "spec": spec,
        "marketing_copy": marketing_copy
    }
)

# Step 7: QA Agent reviews everything
qa_verdict = run_qa_agent()

# Step 8: CEO acts on QA verdict — FEEDBACK LOOP 2
print("\n CEO: Processing QA verdict...")
ceo_qa_messages = get_messages("ceo")

if qa_verdict == "fail":
    print("\n CEO: QA failed — sending revision request to Engineer Agent...")
    send_message(
        from_agent="ceo",
        to_agent="engineer",
        message_type="revision_request",
        payload={
            "feedback": "QA agent found issues with the landing page. Please review the PR comments and revise.",
            "pr_url": pr_url
        }
    )
    print(" CEO: Revision request sent to Engineer Agent")
else:
    print("\n CEO: QA passed — sending final summary to Slack!")

# Step 9: CEO posts final summary
print("\n CEO: Posting final summary...")
from slack_sdk import WebClient
import os
from dotenv import load_dotenv
load_dotenv()

slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
slack_client.chat_postMessage(
    channel="#launches",
    text="LaunchMind Final Summary",
    blocks=[
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🏁 LaunchMind Run Complete!"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Startup:* CampusRide\n*Status:* All agents completed\n*QA Verdict:* {qa_verdict.upper()} — Revision request sent to Engineer"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*GitHub PR:*\n<{pr_url}|View Pull Request>"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Agents Run:*\nCEO, Product, Engineer, Marketing, QA"
                }
            ]
        }
    ]
)
print(" CEO: Final summary posted to Slack!")

# Print full message log
print_full_log()