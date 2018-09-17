import pandas as pd
from cssutils import parseStyle
from bs4 import BeautifulSoup as BeautifulSoupPre
def BeautifulSoup(*args, **kwargs):
    kwargs.setdefault('features', 'lxml')
    return BeautifulSoupPre(*args, **kwargs)


class NodeFrame(object):

    def __init__(self, df=None, load_time=None, metadata=None):

        # TODO?
        # https://www.kaggle.com/arjanso/reducing-dataframe-memory-size-by-65
        self.df = df
        self.metadata = metadata
        self._load_time = load_time

    def set_load_time(self, t):
        self._load_time = t
    
    @property
    def load_time(self):
        return self._load_time
    
    @property
    def memory_usage(self):
        return self.df.memory_usage(deep=True).sum()

    @property
    def table(self):
        return self.df

    def to_html(self, columns=None):

        if columns is None:
            columns = self.df.columns
        
        table_class = "display"
        table_html = self.df[columns].to_html(classes=[table_class], index=False)
        table_html_bs = table_html_bs = BeautifulSoup(table_html).table
        style = parseStyle(table_html_bs.thead.tr['style'])
        style['text-align'] = 'center'
        table_html_bs.thead.tr['style'] = style.cssText

        return str(table_html_bs)

    def __str__(self):

        with pd.option_context('display.max_rows', 11, 'display.max_columns', 10):
            return str(self.df)
    
    @property
    def columns(self):
        return [str(x) for x in self.df.columns]

    def describe(self, **kwargs):
        return self.df.describe(**kwargs)