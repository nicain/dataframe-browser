import pandas as pd
from cssutils import parseStyle
from utilities import BeautifulSoup, fn_timer, generate_uuid, one
import json
from flask import flash

from dataframe_browser.mappers import mapper_library_dict

# TODO: Move to utilities
def memory_usage(df, deep=True):
    return df.memory_usage(deep=deep).sum()

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
    def table(self):
        return self.df

    def to_html(self, columns=None, max_size=5000000):

        if columns is None:
            columns = self.df.columns
        
        table_class = "display"

        old_width = pd.get_option('display.max_colwidth')
        pd.set_option('display.max_colwidth', -1)

        df = self.df[columns]

        print memory_usage(df, deep=True)
        

        if memory_usage(df, deep=True) > max_size:
            flash('Warning: table too large to render; showing summary table instead', category='warning')
            df_to_render = df.describe(include='all').T
            df_to_render.index.name = 'column'
            df_to_render = df_to_render.reset_index()
        else:
            df_to_render = df
        table_html = df_to_render.to_html(classes=[table_class], index=False, escape=False, justify='center')

        pd.set_option('display.max_colwidth', old_width)


        return table_html

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
    def pivot(self, by=None, reduce='squeeze'):

        mapper = mapper_library_dict[reduce]

        data_dict = {}
        for key, df in self.df.groupby(by):
            data_dict[key] = df.T.apply(mapper, axis=1).drop(by)

        # for key, val in data_dict[key].items():
        #     print key, val

        # if squeeze == True:
        #     for key, val in data_dict.items():
        #         set_val = set(*val)
        #         if len(set_val) == 1:
        #             data_dict[key] = one(set_val)

        tmp = pd.DataFrame(data_dict)
        if isinstance(by, list) and len(by) == 1:
            by=one(by)
        tmp.columns = tmp.columns.rename(by)
        return tmp.T.reset_index()

    @fn_timer
    def drop(self, columns=None):
        return self.df.drop(columns, axis=1)

    @fn_timer
    def keep(self, columns=None):
        if isinstance(columns, (str, unicode)):
            return self.df[[columns]]
        else:
            return self.df[columns]

    @fn_timer
    def apply(self, **kwargs):

        if kwargs.get('lazy', True):


            def apply_fcn(col_val):

                payload = {'mapper':str(kwargs['mapper']), 'args':[str(col_val)], 'kwargs':{}}

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
            apply_fcn = mapper_library_dict[kwargs['mapper']]

        result_series = self.df[kwargs['column']].apply(apply_fcn, axis=1)

        df = pd.DataFrame({kwargs['new_column']:result_series})
        return df.join(self.df)
