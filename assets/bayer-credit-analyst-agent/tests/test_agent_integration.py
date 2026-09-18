"""
Integration test: end-to-end agent invocation with mocked tools and LLM.
Tests that the agent starts, accepts queries, and returns structured responses.
"""
import asyncio
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# Set testing flag before importing agent components
os.environ["IBD_TESTING"] = "true"


@pytest.fixture
def mock_tools():
    """Return an empty tool list for offline testing."""
    return []


@pytest.mark.asyncio
async def test_agent_invoke_returns_response(mock_tools):
    """Agent invoke completes and returns a structured response."""
    from agent import SampleAgent, AgentResponse
    agent = SampleAgent()
    result = await agent.invoke(
        query="What is the credit block status for customer 1000001?",
        context_id="test-context-001",
        tools=mock_tools,
    )
    assert isinstance(result, AgentResponse)
    assert result.status in ("completed", "error", "input_required")
    assert isinstance(result.message, str)
    assert len(result.message) > 0


@pytest.mark.asyncio
async def test_agent_stream_yields_chunks(mock_tools):
    """Agent stream yields at least one chunk."""
    from agent import SampleAgent
    agent = SampleAgent()
    chunks = []
    async for chunk in agent.stream(
        query="Analyze TRM utilization for BP 9876543",
        context_id="test-context-002",
        tools=mock_tools,
    ):
        chunks.append(chunk)
    assert len(chunks) >= 1
    last = chunks[-1]
    assert "is_task_complete" in last
    assert "content" in last


@pytest.mark.asyncio
async def test_agent_responds_to_t1_query(mock_tools):
    """Agent handles T1 credit block query format."""
    from agent import SampleAgent
    agent = SampleAgent()
    result = await agent.invoke(
        query="T1: Explain why sales order 1234567890 is blocked",
        context_id="test-t1-001",
        tools=mock_tools,
    )
    assert result.status in ("completed", "error")


@pytest.mark.asyncio
async def test_agent_responds_to_t5_query(mock_tools):
    """Agent handles T5 seasonal financing query format."""
    from agent import SampleAgent
    agent = SampleAgent()
    result = await agent.invoke(
        query="T5: Is customer 2000002 eligible for seasonal financing?",
        context_id="test-t5-001",
        tools=mock_tools,
    )
    assert result.status in ("completed", "error")


def test_agent_instantiates_without_error():
    """Agent class can be instantiated without exceptions."""
    from agent import SampleAgent
    agent = SampleAgent()
    assert agent is not None
    assert agent.llm is not None


def test_system_prompt_contains_required_elements():
    """System prompt includes all required guardrail and task type references."""
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "READ-ONLY" in prompt.upper() or "read-only" in prompt.lower()
    assert "G1" in prompt
    assert "G8" in prompt
    assert "T1" in prompt
    assert "T5" in prompt
    assert "Tier 1" in prompt or "TIER 1" in prompt.upper() or "tier 1" in prompt.lower()
    assert "Tier 3" in prompt or "TIER 3" in prompt.upper() or "tier 3" in prompt.lower()
