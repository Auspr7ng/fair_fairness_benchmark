"""All entry points share the same model/fallback decision."""
import pytest
from unittest.mock import patch

import eval_metrics as api
from eval_metrics.__main__ import main
from eval_metrics.extraction import PaperContent
from eval_metrics.sections import split_sections


@pytest.mark.parametrize('names,reason', [(['F1 score'], None), (None, 'model failed'), ([], None)])
def test_api_and_cli_share_selection(names, reason, capsys):
    paper = PaperContent(split_sections('Experiments\nWe report accuracy and F1.'))
    with patch.object(api, 'extract_paper', return_value=paper), \
         patch('eval_metrics.__main__.extract_paper', return_value=paper), \
         patch.object(api, 'llm_metrics', return_value=(names, reason)):
        if reason:
            with pytest.warns(UserWarning, match=reason):
                expected = api.extract_eval_metrics('paper.pdf')
        else:
            expected = api.extract_eval_metrics('paper.pdf')
        assert main(['paper.pdf']) == 0
        output = capsys.readouterr()
        assert output.out.splitlines() == expected
        assert (reason or '') in output.err


def test_dictionary_only_skips_model_and_retains_verbose_evidence():
    paper = PaperContent(split_sections('Experiments\nWe report accuracy.'))
    with patch.object(api, 'llm_metrics') as model:
        result = api.select_metrics(paper, use_llm=False)
    model.assert_not_called()
    assert result.source == 'dictionary'
    assert result.reason is None
    assert result.names == ['Accuracy']
    assert result.scores[0].name == 'Accuracy'
