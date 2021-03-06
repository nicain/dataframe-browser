import uuid
import logging
import functools
import time
import pandas as pd
from customexceptions import UnrecognizedFileTypeException
from bs4 import BeautifulSoup as BeautifulSoupPre
from future.utils import raise_from
import sqlalchemy
import sqlparse

def generate_uuid(length=32):
    '''https://gist.github.com/admiralobvious/d2dcc76a63df866be17f'''

    u = uuid.uuid4()
    return u.hex[:length]

def create_class_logger(cls, **kwargs):

    level = kwargs.get('level', logging.INFO)
    name = kwargs.get('name', cls.__name__)
    handler = kwargs.get('handler', logging.StreamHandler())
    formatter = kwargs.get('formatter', logging.Formatter(logging.BASIC_FORMAT))

    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level) 

    return logger

def fn_timer(function):
    @functools.wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        return result, t1-t0
    return function_timer

@fn_timer
def load_file(filename, **kwargs):

    index_col = kwargs.get('index_col', None)
    sheet_name = kwargs.get('sheet_name', 0)
    header = kwargs.get('header', 0)

    if filename.endswith('.csv'):
        df = pd.read_csv(filename, index_col=index_col)
    elif filename.endswith('.p'):
        df = pd.read_pickle(filename)
    elif filename.endswith('.xls') or filename.endswith('.xlsx'):
        df = pd.read_excel(filename, sheet_name=sheet_name, index_col=index_col, header=header)
    else:
        raise UnrecognizedFileTypeException(filename)
    
    return df

@fn_timer
def read_file_query_uri(query=None, uri=None):
    query = ''.join([i if ord(i) < 128 else ' ' for i in query])
    query = sqlparse.format(query, strip_comments=True).strip() # Comments with % can also break pandas :/
    if len(query) == 0:
        raise RuntimeError('Cannot read an empty query!')
    query = sqlalchemy.text(query)



    return pd.read_sql_query(query,con=uri)

def one(x, exc_tp=TypeError):
    try:
        val, = x
        return val
    except TypeError as e:
        raise_from(exc_tp, e)


def BeautifulSoup(*args, **kwargs):
    kwargs.setdefault('features', 'lxml')
    return BeautifulSoupPre(*args, **kwargs)