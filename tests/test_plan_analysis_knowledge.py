"""/plan-analysis cites the knowledge each requirement rests on (OdooDots N6.2, 2026-10-29).

Seen on a hosted run: the agent read the customer's OKF bundle but requirements.md cited it
nowhere, because the workflow never asked for it.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / "plugin/skills/CommandingSystem/plan_analysis_workflow.md").read_text()
PRD = (ROOT / "plugin/skills/PRD-Writing/SKILL.md").read_text()


def test_workflow_has_a_knowledge_step():
    assert "## STEP 6b: Knowledge Lookup" in WORKFLOW
    for place in ("knowledge/", "/knowledge/customers/", "index.md"):
        assert place in WORKFLOW, place


def test_each_requirement_cites_its_knowledge():
    assert "Knowledge:" in WORKFLOW
    assert "every functional requirement" in WORKFLOW
    assert "Knowledge: none found" in WORKFLOW


def test_prd_writing_asks_for_the_citation():
    assert "Knowledge:" in PRD and "requirement" in PRD
