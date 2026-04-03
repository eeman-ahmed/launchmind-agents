import anthropic
import os
import json
import base64
import requests
from dotenv import load_dotenv
from message_bus import send_message, get_messages

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def call_llm(system_prompt, user_prompt):
    """Call Claude API and return the response text"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

def generate_html(spec):
    """Use LLM to generate a complete HTML landing page"""
    print("\n ENGINEER AGENT: Generating HTML landing page...")

    system_prompt = """You are a frontend engineer. Generate a complete, 
    beautiful HTML landing page for a startup.
    
    Requirements:
    - Include a headline and subheadline
    - Include a features section showing all product features
    - Include a call-to-action button
    - Include basic CSS styling (modern, clean, professional)
    - Make it mobile-friendly
    - Everything in a single HTML file
    
    Respond with ONLY the HTML code, nothing else. No explanations."""

    user_prompt = f"""Create a landing page for this startup:
    
    Value Proposition: {spec['value_proposition']}
    
    Features:
    {json.dumps(spec['features'], indent=2)}
    
    User Personas:
    {json.dumps(spec['personas'], indent=2)}
    
    Make it professional and compelling."""

    html = call_llm(system_prompt, user_prompt)

    # Clean response
    html = html.strip()
    if html.startswith("```"):
        html = html.split("```")[1]
        if html.startswith("html"):
            html = html[4:]
    html = html.strip()
    if html.endswith("```"):
        html = html[:-3]

    print(" ENGINEER AGENT: HTML generated successfully")
    return html

def get_main_sha():
    """Get the SHA of the main branch"""
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/git/refs/heads/main",
        headers=HEADERS
    )
    return r.json()['object']['sha']

def create_branch(branch_name, sha):
    """Create a new branch from main"""
    print(f"\n ENGINEER AGENT: Creating branch '{branch_name}'...")
    r = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/git/refs",
        headers=HEADERS,
        json={
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
    )
    if r.status_code == 201:
        print(f" ENGINEER AGENT: Branch created successfully")
        return True
    else:
        print(f" ENGINEER AGENT: Branch may already exist, continuing...")
        return True

def commit_file(branch_name, html_content):
    """Commit the HTML file to the branch"""
    print(f"\n ENGINEER AGENT: Committing HTML file to GitHub...")

    content_base64 = base64.b64encode(html_content.encode()).decode()

    # Check if file already exists on this branch
    existing_sha = None
    check = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html",
        headers=HEADERS,
        params={"ref": branch_name}
    )
    if check.status_code == 200:
        existing_sha = check.json()['sha']
        print("   File exists, updating it...")

    payload = {
        "message": "Add CampusRide landing page",
        "content": content_base64,
        "branch": branch_name,
        "author": {
            "name": "EngineerAgent",
            "email": "agent@campusride.ai"
        }
    }

    if existing_sha:
        payload["sha"] = existing_sha

    r = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html",
        headers=HEADERS,
        json=payload
    )

    if r.status_code in [200, 201]:
        print(" ENGINEER AGENT: File committed successfully")
        return True
    else:
        print(f" ENGINEER AGENT: Commit failed: {r.json()}")
        return False

def create_github_issue(spec):
    """Create a GitHub issue for the landing page task"""
    print("\n ENGINEER AGENT: Creating GitHub issue...")

    issue_body = call_llm(
        "You are a software engineer writing a GitHub issue. Be concise and technical.",
        f"Write a GitHub issue description for building a landing page for this product: {spec['value_proposition']}. Include acceptance criteria."
    )

    r = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues",
        headers=HEADERS,
        json={
            "title": "Initial landing page for CampusRide",
            "body": issue_body,
            "labels": []
        }
    )

    if r.status_code == 201:
        issue_url = r.json()['html_url']
        print(f" ENGINEER AGENT: Issue created: {issue_url}")
        return issue_url
    else:
        print(f" ENGINEER AGENT: Issue creation failed: {r.json()}")
        return None

def open_pull_request(branch_name, spec):
    """Open a pull request on GitHub, or return existing one"""
    print("\n ENGINEER AGENT: Opening pull request...")

    # Check if PR already exists
    existing = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/pulls",
        headers=HEADERS,
        params={"head": f"eeman-ahmed:{branch_name}", "state": "open"}
    )
    if existing.status_code == 200 and len(existing.json()) > 0:
        pr_url = existing.json()[0]['html_url']
        print(f" ENGINEER AGENT: PR already exists: {pr_url}")
        return pr_url

    pr_body = call_llm(
        "You are a software engineer writing a pull request description. Be concise.",
        f"Write a pull request description for a landing page built for this startup: {spec['value_proposition']}. Mention what was built and why."
    )

    r = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/pulls",
        headers=HEADERS,
        json={
            "title": "Initial landing page - CampusRide",
            "body": pr_body,
            "head": branch_name,
            "base": "main"
        }
    )

    if r.status_code == 201:
        pr_url = r.json()['html_url']
        print(f" ENGINEER AGENT: Pull request opened: {pr_url}")
        return pr_url
    else:
        print(f" ENGINEER AGENT: PR failed: {r.json()}")
        return None

def run_engineer_agent():
    """Main engineer agent function"""
    print("\n" + "="*60)
    print(" ENGINEER AGENT STARTING")
    print("="*60)

    # Get messages from inbox
    messages = get_messages("engineer")

    if not messages:
        print(" ENGINEER AGENT: No messages found")
        return None

    # Get the product spec from message
    task_message = messages[0]
    spec = task_message["payload"]["spec"]

    print(f" ENGINEER AGENT: Received product spec from Product Agent")
    print(f"   Building for: {spec['value_proposition']}")

    # Step 1: Generate HTML using LLM
    html_content = generate_html(spec)

    # Step 2: Get main branch SHA
    sha = get_main_sha()

    # Step 3: Create new branch
    branch_name = "agent-landing-page"
    create_branch(branch_name, sha)

    # Step 4: Commit HTML file
    commit_success = commit_file(branch_name, html_content)

    if not commit_success:
        print(" ENGINEER AGENT: Failed to commit file")
        return None

    # Step 5: Create GitHub issue
    issue_url = create_github_issue(spec)

    # Step 6: Open pull request
    pr_url = open_pull_request(branch_name, spec)

    if pr_url:
        # Send results back to CEO
        send_message(
            from_agent="engineer",
            to_agent="ceo",
            message_type="result",
            payload={
                "status": "completed",
                "pr_url": pr_url,
                "issue_url": issue_url,
                "branch": branch_name,
                "message": "Landing page built and PR opened"
            },
            parent_message_id=task_message["message_id"]
        )
        print(f"\n ENGINEER AGENT: All done!")
        print(f"   PR: {pr_url}")
        print(f"   Issue: {issue_url}")

    return pr_url