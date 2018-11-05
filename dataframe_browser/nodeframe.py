import pandas as pd
from cssutils import parseStyle
from utilities import BeautifulSoup, fn_timer, generate_uuid, one
from .mappers import mapper_library_dict
import json
from flask import flash
import numpy as np
import copy
import dill
import collections

# TODO: Move to utilities
def memory_usage(df, deep=True):
    return df.memory_usage(deep=deep).sum()


class InteriorSeries(object):

    def __init__(self, series):
        self.series = series

    def summary_html(self):

        ddf = pd.DataFrame({'':self.series}).describe(percentiles=[], include='all').T
        for col in ['top', 'std', '50%', 'mean']:
            if col in ddf.columns:
                ddf.drop(col, axis=1, inplace=True)
        ddf['count'] = ddf['count'].apply(lambda x: '%i' % x)
        for col in ['max', 'min']:
            if col in ddf.columns:
                if self.series.dtype in [int, np.int]:
                    ddf[col] = ddf[col].apply(lambda x: "{0: 3d}".format(int(x)))
                else:
                    ddf[col] = ddf[col].apply(lambda x: "{0: 3.2f}".format(x))
            html = ddf.T.to_html(classes=['interior-series'])

        return html

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

    def __init__(self, df=None, load_time=None, metadata=None, hinge_dict=None):

        # TODO?
        # https://www.kaggle.com/arjanso/reducing-dataframe-memory-size-by-65
        self.df = df
        self.metadata = metadata
        self._load_time = load_time

        if hinge_dict is None:
            self.hinge_dict = collections.defaultdict(list)
        else:
            self.hinge_dict = {key:[val for val in val_list] for key, val_list in hinge_dict.items()}        

    def add_hinge(self, column=None, uuid=None):
        self.hinge_dict[column].append(uuid)

    def transfer_hinges(self, other, col_map=None):
        for col_other, val_list in other.hinge_dict.items():
            if not col_map is None:
                col_other = col_map.get(col_map, col_map)
            for val in val_list:
                if not val in self.hinge_dict[col_other]:
                    self.hinge_dict[col_other].append(val)
            

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

    def to_html(self, frame_index=None, columns=None, max_size=5000000, interactive=True, master_hinge_dict={}):

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

        if interactive == True:

            button_load = '''
            <td><div class="dropdown">
                <button data-toggle="dropdown" class="dropdown-toggle btn btn-light btn-sm py-1 ml-1 col-btn my-1"><span class="oi oi-menu"></span></button>
                <div class="dropdown-menu">
                    {menu_items}
                    <form class="form-inline" action="/command/{session_uuid}/" method="POST">
                        <input type="hidden" name='columns' value='{column_string}'>
                        <input type="hidden" name='frames' value='{frame_index}'>
                        <input type="hidden" name='command' value='drop'>
                        <button type="submit" class="w-100 btn btn-danger btn-sm mx-2 my-1"><span class="oi oi-x"></span> Drop</button>
                    </form>
                </div>
            </div></td>
            '''
            
            bs = BeautifulSoup(table_html)
            table_bs = bs.table
            head = table_bs.thead
            head_row = head.tr
            head_row.insert_after(copy.copy(head_row))
            for x in head_row.find_all('th'):
                column_string = str(x.string)
                menu_item_list = []
                if column_string in self.hinge_dict:
                    for hing_uuid in self.hinge_dict[column_string]:
                        hinge = master_hinge_dict.get(hing_uuid, None)
                        if hinge is not None:
                            menu_item_list.append(hinge.get_menu_html())
                    
                button_load_menu = button_load.format(menu_items='/n'.join(menu_item_list),session_uuid='{session_uuid}', column_string='{column_string}', frame_index='{frame_index}')
                x.replace_with(BeautifulSoup(button_load_menu.format(session_uuid='{{session_uuid}}', 
                                                                column_string=column_string, 
                                                                frame_index=frame_index,
                                                                )))
            table_html = str(table_bs)


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
    def fold(self, by=None, reduce=None):

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
                                                                                                        url : "http://nicholasc-ubuntu:5050/lazy_formatting/{session_uuid}",\
                                                                                                        data: JSON.stringify({payload}, null, "\t"),\
                                                                                                        contentType: "application/json;charset=UTF-8",\
                                                                                                        success: function(result) {{\
                                                                                                                                $("#{id}").html(JSON.parse(result)["result"]);\
                                                                                                                                    console.log("HW");\
                                                                                                                                    }}\
                                                                                                        }});\
                                                                                                }};\
                                                                }});'.format(id=id, payload=json.dumps(payload), session_uuid='{{session_uuid}}')
    
                
                js_txt = """<script>{js}</script>""".format(js=js)

                f = ''.join([div_txt, js_txt])

                return f

        else:

            # Will still need for non-server mode (aka lazy=false)
            if kwargs.get('dillify', False):
                apply_fcn = dill.loads(kwargs['mapper'].encode('latin1'))
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
