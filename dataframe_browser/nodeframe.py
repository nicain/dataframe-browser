import pandas as pd
from cssutils import parseStyle
from utilities import BeautifulSoup, fn_timer


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

        old_width = pd.get_option('display.max_colwidth')
        pd.set_option('display.max_colwidth', -1)

        table_html = self.df[columns].to_html(classes=[table_class], index=False, escape=False)
        pd.set_option('display.max_colwidth', old_width)
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

    @fn_timer
    def groupby(self, **kwargs):
        return {key:df for key, df in self.df.groupby(**kwargs)}

    @fn_timer
    def merge(self, other, **kwargs):
        return self.df.merge(other.df, **kwargs)

    @fn_timer
    def query(self, **kwargs):
        query = kwargs.pop('query')
        return self.df.query(query, **kwargs)

    @fn_timer
    def apply(self, **kwargs):
        result_series = self.df[kwargs['column']][range(5)].apply(kwargs['mapper_fcn'])
        df = pd.DataFrame({kwargs['new_column']:result_series})
        return df.join(self.df)
