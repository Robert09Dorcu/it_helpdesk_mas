# IT Helpdesk MAS

A multi-agent system built with [Google ADK](https://google.github.io/adk-docs/) that automates first-level triage and resolution of IT support tickets.

## Overview

IT departments receive a constant stream of repetitive requests (password resets, Wi-Fi issues, software installs, etc.) that normally require a human to read, classify, and route. This project automates that workflow with a team of cooperating agents, and also detects when an issue category becomes recurring across the organization, flagging it for a systemic fix instead of only closing individual tickets.

## Architecture

A coordinator agent routes each request through a chain of specialized agents, each handing off to the next once its part is done:

```
User → Coordinator → Triage Agent → Resolution Agent → Insights Agent
```

| Agent | Responsibility | Tools |
|---|---|---|
| Coordinator | Entry point; always hands off new requests to Triage | — |
| Triage | Classifies category and priority, logs the ticket | `log_ticket` |
| Resolution | Looks up a known fix or escalates to a human | `search_knowledge_base`, `escalate_to_human` |
| Insights | Checks whether the issue category is recurring org-wide | `analyze_recurring_issues` |

The full flow, including every tool call, is visible live in the ADK web UI's "Events" tab.

## Getting Started

### Prerequisites

- Python 3.10+
- A Google AI Studio API key: https://aistudio.google.com/apikey

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

```bash
cp it_helpdesk_agent/.env.example it_helpdesk_agent/.env
# edit .env and set GOOGLE_API_KEY
```

### Run

```bash
adk web
```

Open the printed URL (defaults to `http://localhost:8000`), select `it_helpdesk_agent` from the dropdown, and start chatting.

## Example

> "I can't connect to Wi-Fi, I've been stuck for two hours."

The system classifies it as a network issue with high priority, logs the ticket, finds a known fix, and replies with the solution. If the same category comes up again later in the session, the Insights agent appends an internal note recommending a systemic fix (e.g. upgrading network infrastructure).

## Project Structure

```
it_helpdesk_mas/
├── it_helpdesk_agent/
│   ├── agent.py         # Agents, tools, and in-memory knowledge base
│   ├── __init__.py
│   └── .env.example
├── requirements.txt
└── README.md
```

## Possible Improvements

- Replace the in-memory ticket log and keyword-based knowledge base with persistent storage and embeddings-based search
- Add a feedback agent that follows up after resolution
- Integrate with a real ticketing system (Jira, Zendesk, ServiceNow)
- Add automated tests and an ADK eval suite for agent behavior
