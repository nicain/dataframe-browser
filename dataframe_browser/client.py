import requests

class Cursor(object):

    def __init__(self, port=5000, hostname='nicholasc-ubuntu', session_uuid=None):

        import uuid
        uuid_length = 32

        if session_uuid is None:
            u = uuid.uuid4()
            session_uuid = u.hex[:uuid_length]

        self.port = port
        self.hostname = hostname
        self.session_uuid = session_uuid
        self._nodedata_and_uuid = None
    
    def uri_template(self, include_session_uuid=True):
        if include_session_uuid == True:
            return 'http://{hostname}:{port}/{base}/{session_uuid}/'.format(base='{base}', hostname=self.hostname, port=self.port, session_uuid=self.session_uuid)
        else:
            return 'http://{hostname}:{port}/{base}/'.format(base='{base}', hostname=self.hostname, port=self.port)

    def uri(self, base='active', include_session_uuid=True):
        return self.uri_template(include_session_uuid=include_session_uuid).format(base=base)

    @staticmethod
    def cell_width(width='90%'):
        from IPython.display import HTML, display
        return display(HTML("<style>.container {{ width:{width} !important; }}</style>".format(width=width)))

    def get_iframe(self, base='browser', height=350, width=None):
        if width is None:
            return '''<iframe  style="width: 100%; border: none" src={uri} height={height}></iframe>'''.format(uri=self.uri_template().format(base=base), height=height)
        else:
            return '''<iframe  style="border: none" src={uri} width={width} height={height}></iframe>'''.format(uri=self.uri_template().format(base=base), width=width, height=height)


    def display(self, base='browser', width=None, height=500):
        from IPython.display import HTML
        return HTML(self.get_iframe(base=base, width=width, height=height))

    def run(self, **kwargs):
        import json
        result = requests.post(self.uri(base='command'), json=json.dumps(kwargs))
        if result.status_code != 200:
            result.raise_for_status()
        if reload and kwargs['command'] != 'reload':
            self.reload()
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
    
    def apply(self, columns=None, mapper=None, new_column=None, lazy=True, reload=True, drop=False):
        return self.run(command='apply', columns=columns, mapper=mapper, new_column=new_column, lazy=lazy, reload=reload, drop=drop)

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
        upload_folder = requests.post(self.uri(base='upload_folder', include_session_uuid=False)).json()['upload_folder']
        server_file_name = "{folder}/{file}".format(folder=upload_folder, file=fname) # dont use os.path because this is a path on the server not client
        requests.post(self.uri(base='upload'), files={'file':(fname, buf)}, data={'filename':[server_file_name], 'command':['open']})
        self.reload()

    @property
    def active_uuid(self):
        import json
        return requests.post(self.uri(base='active_uuid', include_session_uuid=False), json=json.dumps({'session_uuid':self.session_uuid})).json()['active_uuid']

    @property
    def data(self):
        import json
        import pandas as pd

        if self._nodedata_and_uuid is None or self._nodedata_and_uuid[1] != self.active_uuid:
            node_dict = {key:pd.DataFrame(val) for key, val in requests.post(self.uri(base='active')).json().items()}
            if len(node_dict) == 1:
                nodedata = node_dict.values()[0]
            else:
                nodedata = node_dict
            self._nodedata_and_uuid = nodedata, self.active_uuid

        return self._nodedata_and_uuid[0]

    @property
    def stable_url(self):
        node_uuid = requests.get(self.uri(base='node_uuid', include_session_uuid=True)).content
        return '{base}{node_uuid}/'.format(base=self.uri(base='browser', include_session_uuid=True), node_uuid=node_uuid)

    @property
    def help(self):
        print 'HALP' # TODO: rework CLI argparse to print meaningful help


if __name__ == "__main__":

    # This generates a cursor that can be served from the /cursor/<session_uuid>/
    #  out of the save folder, with only basic dependencies on the client environment

    c = Cursor(session_uuid=False)
    
    import dill, os
    save_file_name = os.path.join(os.path.dirname(__file__), 'data', 'cursor.p')

    dill.dump(c, open(save_file_name, 'w'))


 