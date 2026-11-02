import ast
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import pytest

FFB=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def test_header_only_csv_reports_data_error(tmp_path):
    runner=load('runner',FFB/'reproduce/reproduce_resnet18_celeba.py')
    csv=tmp_path/'empty.csv';csv.write_text('pixels,Attractive,Male,Smiling,Wavy_Hair,Young\n')
    with pytest.raises(ValueError,match='no data rows'):runner.sample_rows(csv,20,42)


@pytest.mark.parametrize('option,value',[('--steps','0'),('--batch-size','0'),('--eval-batch-size','-1'),('--lr','nan'),('--lam','nan')])
def test_bad_training_options_rejected_before_imports(monkeypatch,option,value):
    runner=load('runner',FFB/'reproduce/reproduce_resnet18_celeba.py')
    monkeypatch.setattr('sys.argv',['runner',option,value])
    with pytest.raises(SystemExit) as exc:runner.main()
    assert exc.value.code==2


def test_legacy_entrypoint_dispatches_to_real_trainer():
    mod=load('dispatch',FFB/'benchmark/benchmark_tabular.py')
    with patch.object(mod.subprocess,'run') as run:
        run.return_value.returncode=7
        assert mod.main(['--dataset_path','/data/test','--method','erm','--num_training_steps','2'])==7
    command=run.call_args.args[0]
    assert command[1].endswith('ffb_tabular_erm.py')
    assert command[command.index('--data_path')+1]=='/data/test'
    assert command[-2:]==['--num_training_steps','2']
    assert run.call_args.kwargs['cwd']==FFB/'src'


def test_degenerate_metrics_can_be_saved_as_strict_json():
    pytest.importorskip('statsmodels');np=pytest.importorskip('numpy')
    mod=load('fairmetrics',FFB/'src/metrics.py')
    for y,s in [([0,1,0,1],[0,0,0,0]),([0,0,1,1],[0,0,1,1]),([1,1,1,1],[0,0,1,1])]:
        r=mod.metric_evaluation(np.array(y),np.array([.1,.2,.8,.9]),np.array(s),prefix='test')
        assert r['test/aucp'] is None
        assert r['test/eodd'] is None
        assert r['test/acc'] is not None
        json.dumps(r,allow_nan=False)


def test_balanced_metrics_keep_numeric_results():
    pytest.importorskip('statsmodels');np=pytest.importorskip('numpy')
    mod=load('fairmetrics',FFB/'src/metrics.py')
    r=mod.metric_evaluation(np.array([0,1,0,1]),np.array([.1,.9,.2,.8]),np.array([0,0,1,1]),prefix='test')
    assert r['test/acc']==100
    assert r['test/aucp']==0
    json.dumps(r,allow_nan=False)


def test_metric_printing_accepts_undefined_scores():
    # Execute the exact formatting helper without importing the torch-only utilities.
    tree=ast.parse((FFB/'src/utils.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='print_metrics')
    ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'utils','exec'),ns)
    assert ns['print_metrics']({'val/ap':None,'test/ap':92},metrics_print='ap',train=False)==('NA|92.00',)


@pytest.mark.parametrize('trainer',['erm','diffdp'])
@pytest.mark.parametrize('dataset',['adult','german','kdd','compas','bank_marketing','acs'])
def test_dispatched_trainers_actually_use_requested_data_path(trainer,dataset):
    from types import SimpleNamespace
    tree=ast.parse((FFB/f'src/ffb_tabular_{trainer}.py').read_text())
    main=next(n for n in tree.body if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))
    branch=next(n for n in main.body if isinstance(n,ast.If) and ast.unparse(n.test)=="args.dataset == 'adult'")
    calls=[]
    def loader(*args,**kwargs):
        calls.append((args,kwargs));return 'X','y','s'
    ns={'args':SimpleNamespace(dataset=dataset,data_path='/selected/data',sensitive_attr='sex',target_attr='income')}
    for name in ['adult','german','census_income_kdd','compas','bank_marketing','acs']:
        ns['load_'+name+'_data']=loader
    exec(compile(ast.Module(body=[branch],type_ignores=[]),'trainer-data-selection','exec'),ns)
    assert len(calls)==1
    args,kwargs=calls[0]
    assert kwargs.get('path',args[0] if args else None)=='/selected/data'
