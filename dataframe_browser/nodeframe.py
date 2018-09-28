import pandas as pd
from cssutils import parseStyle
from utilities import BeautifulSoup, fn_timer, generate_uuid, one
import json
from flask import flash

# TODO: Move to utilities
def memory_usage(df, deep=True):
    return df.memory_usage(deep=deep).sum()


class InteriorSeries(object):

    def __init__(self, series):
        self.series = series

    def summary_html(self):
        return pd.DataFrame({'':self.series}).describe(percentiles=[], include='all').to_html()

    def to_dict(self):
        return self.series.to_dict()

    def __getitem__(self, ii):
        return self.series[ii]

    def next(self):
        return self.series.next()

    def __iter__(self):
        return self.series.__iter__()


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
        if not isinstance(x, (str, unicode)):
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

    @property
    def formatters(self):
        
        def f(x):
            # print type(x)
            # return str(type(x))+'hi'
            if isinstance(x, InteriorSeries):
                return x.summary_html()
            else:
                return str(x)

            # if isinstance(x, list):
            #     print 'A2'
            #     return pd.DataFrame({'':x[0]}).describe(percentiles=[], include='all').T.to_html()

            # else:
            #     print 'B'
            #     return str(x)

        D = {}
        for key in self.df.columns:
            # D[str(key)] = f
            D[unicode(key)] = f

        return D

    def to_html(self, columns=None, max_size=5000000):

        if columns is None:
            columns = self.df.columns
        
        table_class = "display"

        old_width = pd.get_option('display.max_colwidth')
        pd.set_option('display.max_colwidth', -1)

        df = self.df[columns]        

        if memory_usage(df, deep=True) > max_size:
            flash('Warning: table too large to render; showing summary table instead', category='warning')
            df_to_render = df.describe(include='all').T
            df_to_render.index.name = 'column'
            df_to_render = df_to_render.reset_index()
        else:
            df_to_render = df
        
        table_html = df_to_render.to_html(classes=[table_class], index=False, escape=False, justify='center', formatters=self.formatters)

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
        # Old code...
        # for key, val in data_dict.items():
        #     data_dict[key] = pd.Series([mapper_library_dict[reduce.get(key, None)](x) for x in val], index=val.index)
        #     print
        #     print key
        #     print data_dict[key]
        #     print
        if reduce is None:
            reduce = dict()

        if by is None or len(by) == 0:
    
            def f(x):
                # print x
                return pd.Series(list(x))

            # print '---'
            # blah = self.df.T.apply(f, axis=1)
            # print blah
            # print type(blah)
            # print '===='

            # tmp = pd.DataFrame({'x':[x for x in self.df.iteritems()]})
            final_df = pd.DataFrame({key:[InteriorSeries(col)] for key, col in self.df.iteritems()})
            # final_df = tmp.T.reset_index(drop=True)
            return final_df

        else:
            data_dict = {}
            for key, df in self.df.groupby(by):
                data_dict[key] = df.T.apply(lambda x: InteriorSeries(pd.Series(list(x))), axis=1).drop(by)            

            tmp = pd.DataFrame(data_dict)
            if isinstance(by, list) and len(by) == 1:
                by=one(by)

            tmp.columns = tmp.columns.rename(by)

            final_df = tmp.T.reset_index()

            return final_df

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


            def apply_fcn(args):



                # Marshalling to prepare for payload dumps:
                if isinstance(args, (pd.Series,)):

                    # Multi column; arranged as a series:
                    new_args = [{}]
                    for key, val in args.iteritems():
                        try:
                            new_args[0][key] = val.to_dict()
                        except AttributeError:
                            new_args[0][key] = val

                    args = new_args

                elif isinstance(args, (InteriorSeries,)):
                    args = [args.to_dict()]

                else:
                    
                    # usually a single column with simple data i.e. filename;  need to wrap to unpack with *args in tgt function
                    args = [str(args)]  # str is a unicode guard



                payload = {'mapper':str(kwargs['mapper']), 'args':args, 'kwargs':{}}

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
