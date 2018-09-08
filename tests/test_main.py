from dataframe_browser.dataframebrowser import DataFrameBrowser, UNRECOGNIZED_INPUT_FORMAT
from dataframe_browser.dataframebrowser import TextControllerNonInteractive as TextController
import pandas as pd
import pytest

df = pd.DataFrame({'a':[1,2,3,1,2,2,2], 'b':[.1,.2,.3,.4, .5,.4,.1], 'c':['a', 'b', 'c', 'b', 'a', 'a', 'b']})

@pytest.mark.parametrize('input', [('q:'), ['q:'], 'q:'] )
def test_quit(input):

    with pytest.raises(SystemExit) as pytest_wrapped_exception:
        DataFrameBrowser(controller_class=TextController).run(input=input)
    assert pytest_wrapped_exception.type == SystemExit
    assert pytest_wrapped_exception.value.code == 0

@pytest.mark.parametrize('input', ['blah blah'])
def test_debug(capsys, input):

    DataFrameBrowser(controller_class=TextController).run(input=input)
    out, err = capsys.readouterr()
    stdout_lines = out.splitlines()
    assert '\n'.join(stdout_lines[-2:])==UNRECOGNIZED_INPUT_FORMAT.format(input)




