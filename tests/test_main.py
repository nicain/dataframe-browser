from dataframe_browser.dataframebrowser import DataFrameBrowser, UNRECOGNIZED_INPUT_FORMAT
from dataframe_browser.dataframebrowser import TextControllerNonInteractive as TextController
import pandas as pd
import pytest
import StringIO
import logging
import json

df = pd.DataFrame({'a':[1,2,3,1,2,2,2], 'b':[.1,.2,.3,.4, .5,.4,.1], 'c':['a', 'b', 'c', 'b', 'a', 'a', 'b']})

@pytest.mark.parametrize('input', [('q:'), ['q:'], 'q:'] )
def test_quit(input):

    with pytest.raises(SystemExit) as pytest_wrapped_exception:
        DataFrameBrowser(controller_class=TextController).run(input=input)
    assert pytest_wrapped_exception.type == SystemExit
    assert pytest_wrapped_exception.value.code == 0

@pytest.mark.parametrize('input', ['blah blah'])
def test_stdout(capsys, input):

    DataFrameBrowser(controller_class=TextController).run(input=input)
    out, err = capsys.readouterr()
    stdout_lines = out.splitlines()
    assert '\n'.join(stdout_lines[-2:])==UNRECOGNIZED_INPUT_FORMAT.format(input)

@pytest.mark.parametrize('input', [('blah blah',), ('blah', 'blah')])
def test_logging(input):
    controller_stream = StringIO.StringIO()
    app_stream = StringIO.StringIO()
    formatter = logging.Formatter('["%(levelname)s","%(name)s",%(message)s]')

    controller_kwargs = {'logging_settings':{'handler':logging.StreamHandler(stream=controller_stream),
                                             'formatter': formatter}}
    DataFrameBrowser(controller_class=TextController, 
                     controller_kwargs=controller_kwargs).run(input=input)

    log_lines = controller_stream.getvalue().splitlines()
    assert len(log_lines) == len(input)
    for log_line, input_value in zip(log_lines, input):
        log_dict = json.loads(log_line)
        assert log_dict[2]['unrecognized']['input_value'] == input_value




