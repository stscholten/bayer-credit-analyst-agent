"""Unit tests for business instrumentation functions."""
import logging
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from instrumentation import (
    _emit,
    log_guardrail,
    m1_data_access_verified,
    m1_data_access_failed,
    m2_t1_validated,
    m2_t1_failed,
    m3_t2_t4_validated,
    m3_t2_t4_failed,
    m4_t5_active,
    m4_t5_failed,
    m5_production_validated,
    m5_production_failed,
)


def test_emit_achieved(caplog):
    with caplog.at_level(logging.INFO):
        _emit("M1", True, "test description")
    assert "M1.achieved" in caplog.text
    assert "test description" in caplog.text


def test_emit_missed(caplog):
    with caplog.at_level(logging.INFO):
        _emit("M1", False, "something failed")
    assert "M1.missed" in caplog.text


def test_log_guardrail_triggered(caplog):
    with caplog.at_level(logging.INFO):
        log_guardrail("G1", True, "write attempt detected")
    assert "G1.triggered" in caplog.text
    assert "write attempt" in caplog.text


def test_log_guardrail_passed(caplog):
    with caplog.at_level(logging.INFO):
        log_guardrail("G2", False, "utilization within limit")
    assert "G2.passed" in caplog.text


def test_m1_achieved(caplog):
    with caplog.at_level(logging.INFO):
        m1_data_access_verified(10)
    assert "M1.achieved" in caplog.text
    assert "10" in caplog.text


def test_m1_missed(caplog):
    with caplog.at_level(logging.INFO):
        m1_data_access_failed(["CREDITWORTHINESSQUERY_IN"])
    assert "M1.missed" in caplog.text


def test_m2_achieved(caplog):
    with caplog.at_level(logging.INFO):
        m2_t1_validated()
    assert "M2.achieved" in caplog.text


def test_m2_missed(caplog):
    with caplog.at_level(logging.INFO):
        m2_t1_failed("accuracy 80% below 85% threshold")
    assert "M2.missed" in caplog.text


def test_m3_achieved(caplog):
    with caplog.at_level(logging.INFO):
        m3_t2_t4_validated()
    assert "M3.achieved" in caplog.text


def test_m3_missed(caplog):
    with caplog.at_level(logging.INFO):
        m3_t2_t4_failed("T3", "escalation tier mismatch")
    assert "M3.missed" in caplog.text


def test_m4_achieved(caplog):
    with caplog.at_level(logging.INFO):
        m4_t5_active()
    assert "M4.achieved" in caplog.text


def test_m4_missed(caplog):
    with caplog.at_level(logging.INFO):
        m4_t5_failed("D&B API timeout")
    assert "M4.missed" in caplog.text


def test_m5_achieved(caplog):
    with caplog.at_level(logging.INFO):
        m5_production_validated()
    assert "M5.achieved" in caplog.text


def test_m5_missed(caplog):
    with caplog.at_level(logging.INFO):
        m5_production_failed("G3 not triggered for non-approved instrument")
    assert "M5.missed" in caplog.text
