from dataframe_browser.dataframebrowser import DataFrameBrowser, UNRECOGNIZED_INPUT_FORMAT
from dataframe_browser.dataframebrowser import TextControllerNonInteractive as TextController
import pandas as pd
import pytest
import StringIO
import logging
import json
import os


@pytest.fixture(scope='module')
def df_file_name():
    return os.path.join(os.path.dirname(__file__), 'example.csv')

@pytest.fixture(scope='function')
def df(df_file_name):
    return pd.read_csv(df_file_name, index_col=0)

@pytest.fixture(scope='function')
def dataframe_browser_fixture():

    fixture = {}
    fixture['controller_stream'], fixture['app_stream'] = StringIO.StringIO(), StringIO.StringIO()
    
    formatter = logging.Formatter('["%(levelname)s","%(name)s",%(message)s]')
    controller_kwargs = {'logging_settings':{'handler':logging.StreamHandler(stream=fixture['controller_stream']),
                                             'formatter': formatter}}
    fixture['dataframe_browser'] = DataFrameBrowser(controller_class=TextController, 
                                                    controller_kwargs=controller_kwargs)

    return fixture

@pytest.mark.parametrize('input', [('exit()',), ['exit()'], 'exit()'] )
def test_exit(input):

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
def test_logging(input, dataframe_browser_fixture):

    dataframe_browser_fixture['dataframe_browser'].run(input=input)
    log_lines = dataframe_browser_fixture['controller_stream'].getvalue().splitlines()
    assert len(log_lines) == len(input)
    for log_line, input_value in zip(log_lines, input):
        log_dict = json.loads(log_line)
        assert log_dict[2]['unrecognized']['input_value'] == input_value


@pytest.mark.parametrize('input, expected', [
                                            #  ('blah  ;  blah; blah', 3), 
                                            #  ('blah;blah', 2), 
                                            #  ('blah;', 1), ('blah', 1), 
                                            #  (['blah', 'blah'], 2),
                                             (['blah;blah', 'blah'], 3),
                                             ])
def test_parsing_splitting(input, expected, dataframe_browser_fixture):

    dataframe_browser_fixture['dataframe_browser'].run(input=input)
    log_lines = dataframe_browser_fixture['controller_stream'].getvalue().splitlines()
    assert len(log_lines) == expected


def test_add_file(df_file_name, dataframe_browser_fixture):

    dataframe_browser_fixture['dataframe_browser'].run(input=['o: {0}'.format(df_file_name)])

    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph) == 1


def test_chain_run(df_file_name, dataframe_browser_fixture):
    
    dataframe_browser_fixture['dataframe_browser'].run(input=['o: {0}'.format(df_file_name)]).run(input=['o: {0}'.format(df_file_name)])

    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph) == 2

def test_add_bookmark(df_file_name, dataframe_browser_fixture):

    assert len(dataframe_browser_fixture['dataframe_browser'].model.bookmarks) == 0
    dataframe_browser_fixture['dataframe_browser'].run(input=['o: {0}; b: TEST'.format(df_file_name)])
    assert len(dataframe_browser_fixture['dataframe_browser'].model.bookmarks) == 1

    dataframe_browser_fixture['dataframe_browser'].run(input=['o: {0}; b: TEST'.format(df_file_name)])
    assert len(dataframe_browser_fixture['dataframe_browser'].model.bookmarks) == 1

def test_empty_string_displays_active_df(dataframe_browser_fixture, capsys, df_file_name, df):

    dataframe_browser_fixture['dataframe_browser'].run(input=['o: {0}'.format(df_file_name), ''])
    
    out, err = capsys.readouterr()
    stdout_lines = out.splitlines()
    assert len(stdout_lines) == 2*(len(df)+1)

def test_query(dataframe_browser_fixture, df_file_name):

    dataframe_browser_fixture['dataframe_browser'].run(input='o: {0}; b: TEST'.format(df_file_name))
    assert len(dataframe_browser_fixture['dataframe_browser'].model.active) == 7
    dataframe_browser_fixture['dataframe_browser'].run(input='q: a>1')
    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph.nodes) == 2
    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph.edges) == 1
    assert len(dataframe_browser_fixture['dataframe_browser'].model.active) == 5
    dataframe_browser_fixture['dataframe_browser'].run(input='q: b>.2')
    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph.nodes) == 3
    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph.edges) == 2
    assert len(dataframe_browser_fixture['dataframe_browser'].model.active) == 3

def test_query_compound(dataframe_browser_fixture, df_file_name):
    
    dataframe_browser_fixture['dataframe_browser'].run(input='o: {0}; b: TEST'.format(df_file_name))
    assert len(dataframe_browser_fixture['dataframe_browser'].model.active) == 7
    dataframe_browser_fixture['dataframe_browser'].run(input='q: a>1 and b>.2')
    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph.nodes) == 2
    assert len(dataframe_browser_fixture['dataframe_browser'].model.graph.edges) == 1
    assert len(dataframe_browser_fixture['dataframe_browser'].model.active) == 3

def test_info(dataframe_browser_fixture, df_file_name):

    dataframe_browser_fixture['dataframe_browser'].run(input='o: {0}; i:'.format(df_file_name))