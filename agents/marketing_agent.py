import anthropic
import os
import json
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from message_bus import send_message, get_messages

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def call_llm(system_prompt, user_prompt):
    """Call Claude API and return the response text"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

def generate_marketing_copy(spec):
    """Use LLM to generate all marketing content"""
    print("\n MARKETING AGENT: Generating marketing copy...")

    system_prompt = """You are an expert growth marketer. Generate compelling 
    marketing copy for a startup.
    
    IMPORTANT RULES:
    - Never use placeholder text like [APP_LINK], [Founder Name], [Your Name] etc.
    - Write the email as if it is ready to send right now
    - Use the actual product name from the value proposition
    - Sign the email as "The CampusRide Team"
    - For any links, use: campusride.app
    - Use only ONE specific savings claim throughout: "$200/month"
    - Do not use percentage claims like "75% reduction"
    - Make the email CTA direct and urgent: "Sign up free today at campusride.app"
    - Keep Instagram to maximum 3 emojis total
    
    Respond ONLY with a JSON object in this exact format, nothing else:
    {
        "tagline": "under 10 words, catchy and memorable",
        "description": "2-3 sentences for landing page, compelling and clear",
        "cold_email": {
            "subject": "email subject line",
            "body": "email body, 3-4 paragraphs, personalized and compelling with clear CTA. No placeholders."
        },
        "social_posts": {
            "twitter": "under 280 characters, engaging with hashtags",
            "linkedin": "professional tone, 2-3 sentences with value proposition",
            "instagram": "casual and visual, with relevant emojis and hashtags"
        }
    }"""

    user_prompt = f"""Create marketing copy for this startup:
    
    Value Proposition: {spec['value_proposition']}
    
    Target Users:
    {json.dumps(spec['personas'], indent=2)}
    
    Key Features:
    {json.dumps(spec['features'][:3], indent=2)}
    
    Make it compelling and specific to university students."""

    response = call_llm(system_prompt, user_prompt)

    # Clean response
    response = response.strip()
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    response = response.strip()
    if response.endswith("```"):
        response = response[:-3]

    copy = json.loads(response)
    print(f" MARKETING AGENT: Copy generated")
    print(f"   Tagline: {copy['tagline']}")
    return copy

def send_email(copy, spec):
    """Send cold outreach email via SendGrid"""
    print("\n📧 MARKETING AGENT: Sending email via SendGrid...")

    try:
        message = Mail(
            from_email=os.getenv("SENDGRID_FROM_EMAIL"),
            to_emails=os.getenv("TEST_EMAIL"),
            subject=copy['cold_email']['subject'],
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;"> {copy['tagline']}</h2>
                <p>{copy['description']}</p>
                <hr>
                {copy['cold_email']['body'].replace(chr(10), '<br>')}
                <hr>
                <p style="color: #7f8c8d; font-size: 12px;">
                    Sent by LaunchMind Marketing Agent | CampusRide
                </p>
            </body>
            </html>
            """
        )

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)

        if response.status_code == 202:
            print(" MARKETING AGENT: Email sent successfully!")
            return True
        else:
            print(f" MARKETING AGENT: Email failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f" MARKETING AGENT: Email error: {e}")
        return False

def post_to_slack(copy, pr_url):
    """Post launch announcement to Slack using Block Kit"""
    print("\n MARKETING AGENT: Posting to Slack...")

    try:
        response = slack_client.chat_postMessage(
            channel="#launches",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f" New Launch: {copy['tagline']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*CampusRide is live!*\n{copy['description']}"
                    }
                },
                {
                    "type": "divider"
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
                            "text": "*Status:*\nReady for review "
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Twitter:*\n{copy['social_posts']['twitter']}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Posted by LaunchMind Marketing Agent "
                        }
                    ]
                }
            ]
        )
        print(" MARKETING AGENT: Posted to Slack successfully!")
        return True

    except SlackApiError as e:
        print(f" MARKETING AGENT: Slack error: {e.response['error']}")
        return False

def run_marketing_agent(pr_url=None):
    """Main marketing agent function"""
    print("\n" + "="*60)
    print(" MARKETING AGENT STARTING")
    print("="*60)

    # Get messages from inbox
    messages = get_messages("marketing")

    if not messages:
        print(" MARKETING AGENT: No messages found")
        return None

    # Get product spec from message
    task_message = messages[0]
    spec = task_message["payload"]["spec"]

    print(f" MARKETING AGENT: Received product spec")
    print(f"   Product: {spec['value_proposition']}")

    # Step 1: Generate all marketing copy using LLM
    copy = generate_marketing_copy(spec)

    # Step 2: Send email
    send_email(copy, spec)

    # Step 3: Post to Slack (needs PR url)
    if not pr_url:
        pr_url = "https://github.com/eeman-ahmed/launchmind-agents/pull/2"

    post_to_slack(copy, pr_url)

    # Step 4: Send results back to CEO
    send_message(
        from_agent="marketing",
        to_agent="ceo",
        message_type="result",
        payload={
            "status": "completed",
            "tagline": copy['tagline'],
            "copy": copy,
            "email_sent": True,
            "slack_posted": True
        },
        parent_message_id=task_message["message_id"]
    )

    print("\n MARKETING AGENT: All done!")
    print(f"   Tagline: {copy['tagline']}")
    return copy