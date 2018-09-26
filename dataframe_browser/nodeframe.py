import pandas as pd
from cssutils import parseStyle
from utilities import BeautifulSoup, fn_timer, generate_uuid, one
import json
from flask import flash

# TODO: Move to utilities
def memory_usage(df, deep=True):
    return df.memory_usage(deep=deep).sum()


# TODO: Move to utilities
def hashable(v):
    """Determine whether `v` can be hashed."""
    try:
        hash(v)
    except TypeError:
        return False
    return True

# TODO: Move to utilities
def series_is_index_candidate(s):
    for x in s:
        if not hashable(x):
            return False
        elif not isinstance(s, (str, unicode)):
            return False
    
    return True

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

    def to_html(self, columns=None, max_size=5000000, formatters=None):

        if formatters is None:
            formatters = {}

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
        table_html = df_to_render.to_html(classes=[table_class], index=False, escape=False, justify='center', formatters=formatters)

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
    def fold(self, by=None, reduce=None, mapper_library_dict=None):

        # TODO: Not complete, could have reduce keys separate from by keys... Also need consistent squeezing
        if reduce is None:
            reduce = dict()

        if by is None or len(by) == 0:
    
            tmp = pd.DataFrame({'x':self.df.T.apply(lambda x: list(x), axis=1)})
            return tmp.T.reset_index(drop=True)

        else:
            data_dict = {}
            for key, df in self.df.groupby(by):
                data_dict[key] = df.T.apply(lambda x: list(x), axis=1).drop(by)

            for key, val in data_dict.items():
                data_dict[key] = pd.Series([mapper_library_dict[reduce.get(key, 'squeeze')](x) for x in val], index=val.index)

            tmp = pd.DataFrame(data_dict)
            if isinstance(by, list) and len(by) == 1:
                by=one(by)

            tmp.columns = tmp.columns.rename(by)

            return tmp.T.reset_index()

    @fn_timer
    def drop(self, columns=None):
        if columns is None:
            return self.df.copy()
        else:
            return self.df.drop(columns, axis=1)
            

    @fn_timer
    def keep(self, columns=None):
        if columns is None:
            return self.df.copy()
        elif isinstance(columns, (str, unicode)):
            return self.df[[columns]]
        else:
            return self.df[columns]

    @fn_timer
    def apply(self, **kwargs):

        mapper_library_dict = kwargs['mapper_library_dict']

        if kwargs.get('lazy', True):


            def apply_fcn(col_val):

                # Marshalling to prepare for payload dumps:
                if isinstance(col_val, (pd.Series, pd.DataFrame)):
                    args = [col_val.to_dict()]
                else:#if isinstance(col_val, (str, unicode)):
                    args = [str(col_val)]       # Only a single column specified, need to wrap to unpack with *args in tgt function
                # else:
                    # raise
                    # args = col_val

                # print args
                # raise
                payload = {'mapper':str(kwargs['mapper']), 'args':args, 'kwargs':{}}

                # print kwargs
                # print col_val
                # print payload
                # raise

                id = generate_uuid()
                div_txt = '<div id="{id}"></div>'.format(id=id)
                js = '$(".dataframe").on("draw.dt", function() {{\
                                                                if ($("#{id}").is(":visible") && $("#{id}").is(":empty")  ){{\
                                                                                                $.ajax({{type : "POST",\
                                                                                                        url : "/lazy_formatting",\
                                                                                                        data: JSON.stringify({payload}, null, "\t"),\
                                                                                                        contentType: "application/json;charset=UTF-8",\
                                                                                                        success: function(result) {{\
                                                                                                                                $("#{id}").html(JSON.parse(result)["result"]);\
                                                                                                                                    console.log("HW");\
                                                                                                                                    }}\
                                                                                                        }});\
                                                                                                }};\
                                                                }});'.format(id=id, payload=json.dumps(payload))
    
                
                js_txt = """<script>{js}</script>""".format(js=js)

                f = ''.join([div_txt, js_txt])

                return f

        else:
            apply_fcn = mapper_library_dict[kwargs['mapper']]


        if isinstance(kwargs['columns'], (list,tuple)) and len(kwargs['columns']) > 1:
            result_series = self.df[kwargs['columns']].apply(apply_fcn, axis=1)
        elif isinstance(kwargs['columns'], (list,tuple)) and len(kwargs['columns']) == 1:
            result_series = self.df[one(kwargs['columns'])].apply(apply_fcn)
        else:
            result_series = self.df[kwargs['columns']].apply(apply_fcn)

        df = pd.DataFrame({kwargs['new_column']:result_series})

        df = df.join(self.df)
        if kwargs['drop'] == True:
            df = df.drop(kwargs['columns'], axis=1)

        return df

    @fn_timer
    def transpose(self, index=None, transpose_column_name='fields'):

        if index is None:
            res = (self.df.T).reset_index()
        else:
            res = (self.df.set_index(index).T).reset_index()
            res.columns.name = None
        
        print res.rename(columns={'index':transpose_column_name})
        return res.rename(columns={'index':transpose_column_name})

    @property
    def index_cols(self):

        return [col for col, values in self.df.iteritems() if series_is_index_candidate(values) and len(values.unique()) == len(values)]
        # ...:     print name, len(values.unique())



        # print self.df
        # print self.df.columns
        # print self.df.dtypes
        # self.df['area'].dtype = str
        # desc = self.df.describe( include=['category']).T
        # return [str(c) for c in desc[desc['count']==desc['unique']].index]
