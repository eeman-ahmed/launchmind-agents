# LaunchMind — Multi-Agent Startup System

A Multi-Agent System (MAS) that autonomously runs a micro-startup from idea to execution. Built for FAST NUCES Agentic AI Assignment.

## Startup Idea: CampusRide
A mobile app that helps university students find and share ride carpools to campus, automatically splitting fuel costs in real-time. Target users are university commuter students who want to reduce transportation costs while building campus community.

---

## Agent Architecture# launchmind-agents
STARTUP IDEA (CampusRide)
↓
CEO AGENT (Orchestrator)
/    |         
↓     ↓          ↓
PRODUCT ENGINEER MARKETING
↓         ↓        ↓
└─────────┴────────┘
↓
QA AGENT
↓
CEO AGENT (acts on verdict)

Feedback Loop 1: CEO reviews Product spec and sends revision_request if incomplete

Feedback Loop 2: QA reviews HTML and copy, CEO sends revision_request to Engineer if failed

---

## Agents

| Agent | File | Responsibility |
|-------|------|----------------|
| CEO | agents/ceo_agent.py | Orchestrates all agents, decomposes idea, reviews outputs, acts on feedback |
| Product | agents/product_agent.py | Generates product spec with personas, features, user stories |
| Engineer | agents/engineer_agent.py | Generates HTML landing page, commits to GitHub, opens PR |
| Marketing | agents/marketing_agent.py | Generates copy, sends email via SendGrid, posts to Slack |
| QA | agents/qa_agent.py | Reviews HTML and copy, posts PR comments, sends verdict to CEO |

---

## Platforms

| Platform | What the agents do |
|----------|-------------------|
| GitHub | Engineer creates branch, commits HTML, opens PR. QA posts review comments. |
| Slack | Marketing posts launch announcement. CEO posts final summary. |
| SendGrid | Marketing sends cold outreach email to test inbox. |
| Anthropic Claude API | All agents use claude-haiku-4-5-20251001 for LLM reasoning. |

---

## Real Outputs

- GitHub PR: https://github.com/eeman-ahmed/launchmind-agents/pull/2
- GitHub Issues: Created by Engineer agent on every run
- Slack Workspace: https://join.slack.com/t/launchmind-group/shared_invite/zt-3ue9snx41-ue7EPHgvEgbBbtFahiSxIQ
- Slack Channel: #launches (bot posts launch announcements and CEO summary)
- Email: Sent to test inbox via SendGrid on every run

---

## Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/eeman-ahmed/launchmind-agents.git
cd launchmind-agents
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Copy .env.example to .env and fill in your keys:

ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_pat_here
GITHUB_REPO=your_username/launchmind-agents
SLACK_BOT_TOKEN=your_xoxb_token_here
SENDGRID_API_KEY=your_sg_key_here
SENDGRID_FROM_EMAIL=your_verified_email@gmail.com
TEST_EMAIL=your_email@gmail.com

### 5. Run the system
```bash
python main.py
```

---

## Message Bus

Agents communicate via structured JSON messages through message_bus.py. Every message contains:

- message_id — unique UUID
- from_agent and to_agent — sender and recipient
- message_type — task, result, revision_request, or confirmation
- payload — actual content
- timestamp — ISO 8601 format
- parent_message_id — for traceability

---

## Project Structure
launchmind/
├── agents/
│   ├── ceo_agent.py
│   ├── product_agent.py
│   ├── engineer_agent.py
│   ├── marketing_agent.py
│   └── qa_agent.py
├── main.py
├── message_bus.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
