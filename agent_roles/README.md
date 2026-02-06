# How to Use Your Agent Team

You can orchestrate this team using the **Agent Manager** in Antigravity.

## Instructions
1.  **Open Agent Manager**: Click the robot icon in the sidebar.
2.  **Create New Agent**: Click "Spawn Agent" (or "+").
3.  **Assign Role**:
    - Open the corresponding file in `agent_roles/` (e.g., `agent_roles/tech_lead.md`).
    - Copy the **System Prompt** content.
    - Paste it into the "Instructions" or "Prompt" field of the new agent.
    - Select the recommended model (Pro or Flash) if available.
4.  **Assign Goal**: Give the agent their specific task (e.g., "Review `bot/main.py`").

## Team Roster
| Role | File | Model |
|------|------|-------|
| **Orchestrator** | `agent_roles/orchestrator.md` | Gemini 3 Pro |
| **Tech Lead** | `agent_roles/tech_lead.md` | Gemini 3 Pro |
| **Python Dev** | `agent_roles/python_dev.md` | Gemini 3 Pro |
| **Video Dev** | `agent_roles/video_dev.md` | Gemini 3 Pro |
| **Researcher** | `agent_roles/researcher.md` | Gemini 3 Flash |
| **QA/Debugger** | `agent_roles/qa_debugger.md` | Gemini 3 Pro |

## Pro Tip
You can also ask **me** (your current agent) to adopt one of these personas temporarily if you don't want to spawn a new agent. Just say: *"Act as Tech Lead and review this file."*
