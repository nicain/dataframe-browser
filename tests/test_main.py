from dataframe_browser.dataframebrowser import DataFrameBrowser, TextControllerNonInteractive
import pandas as pd
import pytest

df = pd.DataFrame({'a':[1,2,3,1,2,2,2], 'b':[.1,.2,.3,.4, .5,.4,.1], 'c':['a', 'b', 'c', 'b', 'a', 'a', 'b']})

def test_quit():

    with pytest.raises(SystemExit) as pytest_wrapped_exception:
        DataFrameBrowser(controller_class=TextControllerNonInteractive).run(input=['q:'])
    assert pytest_wrapped_exception.type == SystemExit
    assert pytest_wrapped_exception.value.code == 0





