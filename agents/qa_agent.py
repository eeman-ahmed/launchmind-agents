import anthropic
import os
import json
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

def call_llm(system_prompt, user_prompt, max_tokens=1500):
    """Call Claude API and return the response text"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

def review_html(html_content, spec):
    """Use LLM to review the HTML landing page"""
    print("\n QA AGENT: Reviewing HTML landing page...")

    system_prompt = """You are a senior QA engineer reviewing a landing page.
    Check if the HTML matches the product specification.
    
    Respond ONLY with a JSON object in this exact format, nothing else:
    {
        "verdict": "pass" or "fail",
        "score": number between 1-10,
        "issues": [
            {
                "type": "html",
                "line": "approximate line or section",
                "comment": "specific issue description"
            }
        ],
        "summary": "overall assessment in 2-3 sentences"
    }
    
    Check for:
    - Does headline match the value proposition?
    - Are the key features mentioned?
    - Is there a clear call-to-action?
    - Is the styling professional?
    - Is the content relevant to the product?"""

    user_prompt = f"""Review this HTML landing page against the product spec:
    
    VALUE PROPOSITION: {spec['value_proposition']}
    
    EXPECTED FEATURES:
    {json.dumps([f['name'] for f in spec['features']], indent=2)}
    
    HTML CONTENT:
    {html_content}
    
    Provide specific feedback with at least 2 issues (even minor ones)."""

    response = call_llm(system_prompt, user_prompt, max_tokens=2500)

    # Clean response
    response = response.strip()
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    response = response.strip()
    if response.endswith("```"):
        response = response[:-3]

    review = json.loads(response)
    print(f" QA AGENT: HTML review complete - Score: {review['score']}/10")
    return review

def review_marketing_copy(copy):
    """Use LLM to review marketing copy"""
    print("\n QA AGENT: Reviewing marketing copy...")

    system_prompt = """You are a senior marketing reviewer.
    Review the marketing copy for quality and effectiveness.
    
    Respond ONLY with a JSON object in this exact format, nothing else:
    {
        "verdict": "pass" or "fail",
        "score": number between 1-10,
        "issues": [
            {
                "type": "copy",
                "element": "tagline/email/twitter/linkedin/instagram",
                "comment": "specific issue"
            }
        ],
        "summary": "overall assessment in 2-3 sentences"
    }
    
    Check for:
    - Is the tagline under 10 words and compelling?
    - Does the cold email have a clear CTA?
    - Are social posts platform-appropriate?
    - Is the tone consistent?
    - Any placeholder text remaining?"""

    user_prompt = f"""Review this marketing copy:
    
    {json.dumps(copy, indent=2)}
    
    Provide at least 2 specific issues even if minor."""

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

    review = json.loads(response)
    print(f" QA AGENT: Copy review complete - Score: {review['score']}/10")
    return review

def get_html_from_github(pr_url):
    """Fetch the HTML file from GitHub"""
    print("\n QA AGENT: Fetching HTML from GitHub...")
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html",
        headers=HEADERS,
        params={"ref": "agent-landing-page"}
    )
    if r.status_code == 200:
        import base64
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        print(" QA AGENT: HTML fetched successfully")
        return content
    else:
        print(" QA AGENT: Could not fetch HTML")
        return None

def post_pr_review_comments(pr_url, html_issues, copy_issues):
    """Post review comments on the GitHub PR"""
    print("\n QA AGENT: Posting review comments on GitHub PR...")

    # Get PR number from URL
    pr_number = pr_url.split('/')[-1]

    # Get the latest commit SHA on the PR branch
    commits_r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/commits",
        headers=HEADERS
    )
    if commits_r.status_code != 200:
        print(" QA AGENT: Could not get commits")
        return False

    latest_sha = commits_r.json()[-1]['sha']

    # Post a general review comment
    all_issues = []
    for issue in html_issues[:2]:
        all_issues.append(f"**HTML Issue:** {issue['comment']}")
    for issue in copy_issues[:2]:
        all_issues.append(f"**Copy Issue:** {issue['comment']}")

    review_body = "## QA Agent Review\n\n"
    review_body += "### Issues Found:\n"
    for i, issue in enumerate(all_issues):
        review_body += f"- **Section {i+1}:** {issue}\n"
    review_body += "\n### Recommendation:\n"
    review_body += "Please address the above issues before merging.\n"
    review_body += "\n*Review posted automatically by LaunchMind QA Agent*"

    # Post review on PR
    review_r = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/reviews",
        headers=HEADERS,
        json={
            "commit_id": latest_sha,
            "body": review_body,
            "event": "COMMENT",
            "comments": [
                {
                    "path": "index.html",
                    "position": 1,
                      "body": f" QA Review - Hero Section: {html_issues[0]['comment'] if html_issues else 'Verify headline matches value proposition'}"
                },
                {
                    "path": "index.html",
                    "position": 2,
                    "body": f" QA Review - Features Section: {html_issues[1]['comment'] if len(html_issues) > 1 else 'Verify all 5 features are listed with descriptions'}"
                }
            ]
        }
    )

    if review_r.status_code == 200:
        print(" QA AGENT: Review comments posted on GitHub PR!")
        return True
    else:
        print(f" QA AGENT: Could not post inline comments, posting general comment...")
        # Fallback: post a regular comment
        comment_r = requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/issues/{pr_number}/comments",
            headers=HEADERS,
            json={"body": review_body}
        )
        if comment_r.status_code == 201:
            print(" QA AGENT: General review comment posted!")
            return True
        return False

def run_qa_agent():
    """Main QA agent function"""
    print("\n" + "="*60)
    print(" QA AGENT STARTING")
    print("="*60)

    messages = get_messages("qa")

    if not messages:
        print(" QA AGENT: No messages found")
        return None

    task_message = messages[0]
    payload = task_message["payload"]
    pr_url = payload.get("pr_url")
    spec = payload.get("spec")
    marketing_copy = payload.get("marketing_copy")

    print(f" QA AGENT: Received review task from CEO")
    print(f"   PR to review: {pr_url}")

    try:
        # Step 1: Fetch HTML from GitHub
        html_content = get_html_from_github(pr_url)

        # Step 2: Review HTML
        html_review = None
        if html_content:
            html_review = review_html(html_content, spec)

        # Step 3: Review marketing copy
        copy_review = None
        if marketing_copy:
            copy_review = review_marketing_copy(marketing_copy)

        # Step 4: Post comments on GitHub PR
        if html_review and copy_review and pr_url:
            post_pr_review_comments(
                pr_url,
                html_review.get('issues', []),
                copy_review.get('issues', [])
            )

        # Step 5: Determine overall verdict
        overall_verdict = "pass"
        if html_review and html_review['verdict'] == 'fail':
            overall_verdict = "fail"
        if copy_review and copy_review['verdict'] == 'fail':
            overall_verdict = "fail"

        print(f"\n QA AGENT: Overall verdict: {overall_verdict.upper()}")

        # Step 6: Send report back to CEO
        send_message(
            from_agent="qa",
            to_agent="ceo",
            message_type="result",
            payload={
                "verdict": overall_verdict,
                "html_review": html_review,
                "copy_review": copy_review,
                "pr_url": pr_url,
                "message": f"QA review complete. Overall verdict: {overall_verdict}"
            },
            parent_message_id=task_message["message_id"]
        )

        return overall_verdict

    except Exception as e:
        print(f"\n QA AGENT: Failed with error: {e}")
        send_message(
            from_agent="qa",
            to_agent="ceo",
            message_type="result",
            payload={
                "status": "failed",
                "verdict": "fail",
                "error": str(e),
                "message": "QA agent encountered an error and could not complete the review"
            },
            parent_message_id=task_message["message_id"]
        )
        return None