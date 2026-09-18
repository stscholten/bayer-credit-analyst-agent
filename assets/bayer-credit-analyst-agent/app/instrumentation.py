"""
Business Step Instrumentation — Bayer Credit Analyst Agent

Implements structured logging and OpenTelemetry spans for the 5 PRD milestones.
Log pattern: [MILESTONE_ID].[achieved|missed]: [description]
"""
import logging
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    _tracer = trace.get_tracer("bayer-credit-analyst-agent")
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    _tracer = None


def _emit(milestone_id: str, achieved: bool, description: str) -> None:
    """Emit structured milestone log."""
    status = "achieved" if achieved else "missed"
    logger.info("[%s.%s]: %s", milestone_id, status, description)


@contextmanager
def milestone_span(milestone_id: str, description: str) -> Generator[None, None, None]:
    """Context manager that wraps a business step with a telemetry span."""
    if _OTEL_AVAILABLE and _tracer:
        with _tracer.start_as_current_span(f"milestone.{milestone_id}") as span:
            span.set_attribute("milestone.id", milestone_id)
            span.set_attribute("milestone.description", description)
            try:
                yield
                span.set_status(Status(StatusCode.OK))
                _emit(milestone_id, True, description)
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.record_exception(exc)
                _emit(milestone_id, False, description)
                raise
    else:
        try:
            yield
            _emit(milestone_id, True, description)
        except Exception:
            _emit(milestone_id, False, description)
            raise


def log_guardrail(guardrail_id: str, triggered: bool, detail: str) -> None:
    """Log a guardrail evaluation result."""
    status = "triggered" if triggered else "passed"
    logger.info("GUARDRAIL.%s.%s: %s", guardrail_id, status, detail)


# Milestone-specific helpers

def m1_data_access_verified(source_count: int) -> None:
    _emit("M1", True, f"S/4HANA data access verified across all {source_count} sources for agent initialization")


def m1_data_access_failed(failed_sources: list[str]) -> None:
    _emit("M1", False, f"One or more S/4HANA API connections failed during initialization: {', '.join(failed_sources)}")


def m2_t1_validated() -> None:
    _emit("M2", True, "T1 credit block explanation validated on test case set")


def m2_t1_failed(reason: str) -> None:
    _emit("M2", False, f"T1 explanation accuracy below threshold or guardrail violation detected: {reason}")


def m3_t2_t4_validated() -> None:
    _emit("M3", True, "T2, T3, T4 task types validated and escalation model confirmed")


def m3_t2_t4_failed(failed_task: str, reason: str) -> None:
    _emit("M3", False, f"One or more of T2/T3/T4 failed validation or escalation trigger test: {failed_task} — {reason}")


def m4_t5_active() -> None:
    _emit("M4", True, "T5 seasonal financing eligibility active with D&B integration verified")


def m4_t5_failed(reason: str) -> None:
    _emit("M4", False, f"T5 D&B integration failed or G5 guardrail did not trigger on stale data: {reason}")


def m5_production_validated() -> None:
    _emit("M5", True, "Full escalation model and all 8 guardrails validated in production")


def m5_production_failed(violation: str) -> None:
    _emit("M5", False, f"Escalation tier mismatch or guardrail violation detected in production validation: {violation}")
