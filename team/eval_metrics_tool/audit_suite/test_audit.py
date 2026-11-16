import json
import os
from pathlib import Path
import pytest
from team.eval_metrics_tool.audit_suite.cases import CASES, evaluate
from team.eval_metrics_tool.audit_suite.fixtures import make_fixtures


RESULTS = []


@pytest.fixture(scope="session")
def example_dir():
    directory = Path(os.environ.get("EVAL_AUDIT_OUTPUT","audit_results"))/"examples"
    make_fixtures(directory)
    return directory


@pytest.mark.parametrize("case",CASES,ids=lambda c:c.id)
def test_case(case,example_dir):
    try:
        result = evaluate(case,example_dir)
    except Exception as exc:
        from dataclasses import asdict
        result = {**asdict(case),"actual":{"exception":type(exc).__name__,"message":str(exc)},"passed":False,"evidence":{}}
    RESULTS.append(result)
    assert result["passed"], (f"{case.id}: {case.title}\nExpected: {case.expected!r}\n"
                              f"Observed: {result['actual']!r}\nWhy: {case.why}")


@pytest.fixture(scope="session",autouse=True)
def save_results():
    yield
    directory = Path(os.environ.get("EVAL_AUDIT_OUTPUT","audit_results"))
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"cases.json").write_text(json.dumps(RESULTS,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
