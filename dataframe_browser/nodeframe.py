import pandas as pd
from cssutils import parseStyle
from utilities import BeautifulSoup, fn_timer, generate_uuid
import json

from dataframe_browser.mappers import mapper_library_dict

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

        if kwargs.get('lazy', True):


            def apply_fcn(col_val):

                payload = {'mapper':kwargs['mapper'], 'mapper_library':kwargs['mapper_library'], 'args':[str(col_val)], 'kwargs':{}}

                id = generate_uuid()
                div_txt = '<div id="{id}"></div>'.format(id=id)
                js = '$(".dataframe").on("draw.dt", function() {{\
                                                                if ($("#{id}").is(":visible") && $("#{id}").is(":empty")  ){{\
                                                                                                $.ajax({{type : "POST",\
                                                                                                        url : "/lazy_formatting",\
                                                                                                        data: JSON.stringify({payload}, null, "\t"),\
                                                                                                        contentType: "application/json;charset=UTF-8",\
                                                                                                        success: function(result) {{\
                                                                                                                                    document.getElementById("{id}").innerHTML = JSON.parse(result)["result"];\
                                                                                                                                    console.log("HW");\
                                                                                                                                    }}\
                                                                                                        }});\
                                                                                                }};\
                                                                }});'.format(id=id, payload=payload)
    
                
                js_txt = """<script>{js}</script>""".format(js=js)

                f = ''.join([div_txt, js_txt])

                return f

        else:
            apply_fcn = mapper_library_dict[kwargs['mapper_library']][kwargs['mapper']]

        result_series = self.df[kwargs['column']].apply(apply_fcn)

        df = pd.DataFrame({kwargs['new_column']:result_series})
        return df.join(self.df)
