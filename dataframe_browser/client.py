import requests

class Cursor(object):

    @staticmethod
    def get_new_uuid():
        import uuid
        uuid_length = 32
        return uuid.uuid4().hex[:uuid_length]

    def __init__(self, port=5000, hostname='nicholasc-ubuntu', session_uuid=None, node_uuid=None):

        if session_uuid is None:
            session_uuid = self.get_new_uuid()

        self.port = port
        self.hostname = hostname
        self._session_uuid = session_uuid
        self._node_uuid = node_uuid


    @property
    def node_uuid(self):
        return self._node_uuid

    @property
    def session_uuid(self):
        return self._session_uuid
    
    @property
    def frozen(self):
        if self.node_uuid is None:
            return False
        else:
            return True

    def freeze(self):
        self._node_uuid = self.active_uuid

    def unfreeze(self):
        self._node_uuid = None

    def uri(self, base, session_uuid=None, node_uuid=None):

        uri = 'http://{hostname}:{port}/{base}/'.format(base=base, hostname=self.hostname, port=self.port)
        if session_uuid is not None:
            uri += '{session_uuid}/'.format(session_uuid=session_uuid)
            if node_uuid is not None:
                uri += '{node_uuid}/'.format(node_uuid=node_uuid)

        return uri

    @staticmethod
    def cell_width(width='90%'):
        from IPython.display import HTML, display
        return display(HTML("<style>.container {{ width:{width} !important; }}</style>".format(width=width)))

    def get_iframe(self, base='browser', height=350, width=None, session_uuid=None, node_uuid=None):
        if width is None:
            template = '<iframe  style="width: 100%; border: none" src={uri} height={height}></iframe>'
        else:
            template = '<iframe  style="border: none" src={uri} width={width} height={height}></iframe>'

        return template.format(uri=self.uri(base, session_uuid=session_uuid, node_uuid=node_uuid), height=height)

    def display(self, base='browser', width=None, height=500):
        from IPython.display import HTML
        return HTML(self.get_iframe(base=base, width=width, height=height, session_uuid=self.session_uuid, node_uuid=self.node_uuid))

    def run(self, **kwargs):
        import json
        result = requests.post(self.uri(base='command', session_uuid=self.session_uuid), json=json.dumps(kwargs))
        if result.status_code != 200:
            result.raise_for_status()

        return self

    def open(self, filename=None, index_col=None, reload=True):
        return self.run(command='open', filename=filename, index_col=index_col,reload=reload)

    def read(self, query=None, uri=None, filename=None, reload=True, password=None):
        return self.run(command='read', filename=filename, query=query, uri=uri, reload=reload)

    def query(self, query=None, reload=True):
        return self.run(command='query', query=query, reload=reload)

    def groupby(self, by=None, reload=True):
        return self.run(command='groupby', by=by, reload=reload)

    def fold(self, by=None, reload=True):
        return self.run(command='fold', by=by, reload=reload)

    def drop(self, columns=None, frames=None, reload=True):
        return self.run(command='drop', columns=columns, reload=reload, frames=frames)

    def keep(self, columns=None, frames=None, reload=True):
        return self.run(command='keep', columns=columns, frames=frames, reload=reload)

    def concat(self, how='vertical', reload=True):
        return self.run(command='concat', how=how, reload=reload)
    
    def apply(self, mapper=None, columns=None, new_column=None, lazy=True, reload=True, drop=False):
        import dill
        import six

        if six.PY3:
            raise RuntimeError('apply and update not supported in python3')

        if not isinstance(mapper, six.string_types):
            assert callable(mapper)
            mapper = dill.dumps(mapper).decode('latin1')
            dillify=True
            lazy=False
        else:
            dillify=False

        return self.run(command='apply', mapper=mapper, columns=columns, new_column=new_column, lazy=lazy, reload=reload, drop=drop, dillify=dillify)

    def update(self, mapper=None, column=None, lazy=True, reload=True):
        return self.apply(mapper=mapper, columns=column, new_column=column, lazy=lazy, reload=reload, drop=True)

    def reload(self):
        return self.run(command='reload', reload=True)
    
    def back(self, N=1, reload=True):
        return self.run(command='back', N=N, reload=reload)

    def forward(self, reload=True):
        return self.run(command='forward', reload=reload)

    def bookmark(self, name=None, reload=True):
        return self.run(command='bookmark', name=name, reload=reload)

    def transpose(self, index=None, reload=True):
        return self.run(command='transpose', index=index, reload=reload)

    def upload(self, df, reload=True):
        import json
        import io

        buf = io.BytesIO()
        df.to_pickle(buf)
        buf.seek(0)
        fname = 'file.p'
        upload_folder = requests.post(self.uri(base='upload_folder')).json()['upload_folder']
        server_file_name = "{folder}/{file}".format(folder=upload_folder, file=fname) # dont use os.path because this is a path on the server not client
        requests.post(self.uri(base='upload', session_uuid=self.session_uuid), files={'file':(fname, buf)}, data={'filename':[server_file_name], 'command':['open']})
        self.reload()

    @property
    def active_uuid(self):
        import json
        return requests.post(self.uri(base='active_uuid'), json=json.dumps({'session_uuid':self.session_uuid})).json()['active_uuid']

    @property
    def data(self):
        import json
        import pandas as pd

        if self.node_uuid is None:
            data_endpoint = self.uri(base='data', session_uuid=self.session_uuid)
        else:
            node_uuid = requests.get(self.uri(base='node_uuid', session_uuid=self.session_uuid)).content
            data_endpoint = '{base}{node_uuid}/'.format(base=self.uri(base='data', session_uuid=self.session_uuid), node_uuid=node_uuid)
        
        node_dict = {key:pd.DataFrame(val) for key, val in requests.post(data_endpoint).json().items()}

        if len(node_dict) == 1:
            nodedata = node_dict.values()[0]
        else:
            nodedata = node_dict

        return nodedata

    @property
    def permalink(self):
        node_uuid = requests.get(self.uri(base='node_uuid', session_uuid=self.session_uuid)).content
        return '{base}{node_uuid}/'.format(base=self.uri(base='browser', session_uuid=self.session_uuid), node_uuid=node_uuid)

    def hinge(self, column=None, uuid=None, frames=None, nodes=None, reload=True): 
        return self.run(command='hinge', column=column, uuid=uuid, frames=frames, nodes=nodes, reload=reload) 

    @property
    def help(self):
        pass
        # print 'HALP' # TODO: rework CLI argparse to print meaningful help


if __name__ == "__main__":

    # This generates a cursor that can be served from the /cursor/<session_uuid>/
    #  out of the save folder, with only basic dependencies on the client environment
    import dill, os, six, json

    c = Cursor
    save_file_name = os.path.join(os.path.dirname(__file__), 'data', 'cursor.dill.json') 
    
    if os.path.exists(save_file_name):
        data_dict = json.load(open(save_file_name, 'r'))
    else:
        data_dict = {}
        

    json.dump(data_dict, open(save_file_name, 'w'))

