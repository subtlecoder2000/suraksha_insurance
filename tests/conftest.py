import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.human_queue_manager import reset_queue
from critique.analytics import reset_stats
from data.crm import reset_sample_data
from data.semantic_memory import reset_memory_store
from monitoring.observability import reset_audit_log
from monitoring.scorecard import reset_metrics
from services.workflow_engine import reset_workflows


@pytest.fixture(autouse=True)
def _reset_in_memory_state():
    reset_sample_data()
    reset_memory_store()
    reset_workflows()
    reset_queue()
    reset_audit_log()
    reset_stats()
    reset_metrics()
    yield
    reset_sample_data()
    reset_memory_store()
    reset_workflows()
    reset_queue()
    reset_audit_log()
    reset_stats()
    reset_metrics()
