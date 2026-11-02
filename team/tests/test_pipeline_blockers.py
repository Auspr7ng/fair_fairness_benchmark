import json
import os
from pathlib import Path
from unittest.mock import patch
import pytest
from team.paper_pipeline import run_pipeline
from team.insert_into_record_tool import MetricsRecord, update_record_file
from team.agent.initialization_tool import create_initialization_tool
from team.agent.basic_agent import build_agent, main
from team.agent.tests.test_agent_workflow import ScriptedToolModel
from langchain_core.messages import AIMessage, ToolMessage
import httpx


def test_custom_metric_handoff_and_readback(tmp_path):
    paper = tmp_path/'paper.txt'
    paper.write_text('Experiments\nOur method achieves mean flip rate (mFR) of 4.3%.')
    output = tmp_path/'record.json'
    result = run_pipeline(paper, output, metrics=['mean flip rate (mFR)'])
    assert result['metrics'] == {'mean flip rate (mFR)': 4.3}
    assert result['unresolved'] == []
    assert MetricsRecord.load_json(output).record == result['metrics']
    with pytest.raises(FileExistsError):
        run_pipeline(paper, output, metrics=['mean flip rate (mFR)'])


def test_blank_input_does_not_create_record(tmp_path):
    from team.eval_metrics_tool.eval_metrics.extraction import PaperContent
    from team.eval_metrics_tool.eval_metrics.sections import split_sections
    dest=tmp_path/'record.json'
    with patch('team.paper_pipeline.extract_paper',return_value=PaperContent(split_sections(''))):
        with pytest.raises(ValueError, match='No extractable'):
            run_pipeline('blank.pdf',dest,use_llm=False)
    assert not dest.exists()


def test_replace_failure_preserves_record(tmp_path):
    record=tmp_path/'record.json';MetricsRecord({'Accuracy':92}).save_json(record)
    before=record.read_bytes()
    with patch('team.insert_into_record_tool.insert_into_record.os.replace',side_effect=OSError('disk error')):
        with pytest.raises(OSError): update_record_file(record,'Accuracy',93)
    assert record.read_bytes()==before
    assert list(tmp_path.iterdir())==[record]


def test_serialization_failure_preserves_record(tmp_path):
    record=tmp_path/'record.json';MetricsRecord({'Accuracy':92}).save_json(record)
    with patch('team.insert_into_record_tool.insert_into_record.json.dumps',side_effect=ValueError('bad serialization')):
        with pytest.raises(ValueError):update_record_file(record,'Accuracy',93)
    assert MetricsRecord.load_json(record).record=={'Accuracy':92}


def test_initialization_through_graph_is_bound_to_selected_record(tmp_path):
    record=tmp_path/'selected.json';MetricsRecord({}).save_json(record)
    other=tmp_path/'other.json';MetricsRecord({'Accuracy':7}).save_json(other)
    paper=tmp_path/'paper.txt';paper.write_text('Results\nOur method achieved Accuracy = 92%.')
    model=ScriptedToolModel(responses=[AIMessage(content='',tool_calls=[{
        'name':'initialize_current_record','args':{'pdf_path':str(paper),'metrics':['Accuracy']},'id':'init'}]),
        AIMessage(content='',tool_calls=[{'name':'show_current_record','args':{},'id':'read'}]),AIMessage(content='Done')])
    result=build_agent(record,model=model).invoke({'messages':[('user','Initialize selected record from the paper and read it back.')]})
    replies=[json.loads(m.content) for m in result['messages'] if isinstance(m,ToolMessage)]
    assert replies[0]['metrics']=={'Accuracy':92.0}
    assert replies[1]['metrics']=={'Accuracy':92.0}
    assert MetricsRecord.load_json(other).record=={'Accuracy':7}


def test_unavailable_agent_reports_offline_alternative(monkeypatch,capsys):
    monkeypatch.setattr('sys.argv',['agent'])
    with patch('team.agent.basic_agent.build_agent') as build:
        build.return_value.invoke.side_effect=httpx.ConnectError('refused')
        with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==1
    assert 'team.paper_pipeline' in capsys.readouterr().err
