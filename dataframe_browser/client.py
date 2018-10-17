import requests
import json
import pandas as pd
import uuid
from IPython.display import HTML, display
import io


class Cursor(object):

    def __init__(self, port=5000, hostname='nicholasc-ubuntu', session_uuid=None):

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
        return display(HTML("<style>.container {{ width:{width} !important; }}</style>".format(width=width)))

    def get_iframe(self, base='browser', height=350, width=None):
        if width is None:
            return '''<iframe  style="width: 100%; border: none" src={uri} height={height}></iframe>'''.format(uri=self.uri_template().format(base=base), height=height)
        else:
            return '''<iframe  style="border: none" src={uri} width={width} height={height}></iframe>'''.format(uri=self.uri_template().format(base=base), width=width, height=height)


    def display(self, base='browser', width=None, height=500):
        return HTML(self.get_iframe(base=base, width=width, height=height))

    def run(self, **kwargs):
        result = requests.post(self.uri(base='command'), json=json.dumps(kwargs))
        if result.status_code != 200:
            result.raise_for_status()
        if reload and kwargs['command'] != 'reload':
            self.reload()
        return self

    def open(self, filename=None, reload=True):
        return self.run(command='open', filename=filename, reload=reload)

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

        buf = io.BytesIO()
        df.to_csv(buf)
        buf.seek(0)
        upload_folder = requests.post(self.uri(base='upload_folder', include_session_uuid=False)).json()['upload_folder']
        server_file_name = "{folder}/{file}".format(folder=upload_folder, file='file.csv') # dont use os.path because this is a path on the server not client
        requests.post(self.uri(base='upload'), files={'file':('file.csv', buf)}, data={'filename':[server_file_name], 'command':['open']})
        self.reload()

    @property
    def active_uuid(self):
        return requests.post(self.uri(base='active_uuid', include_session_uuid=False), json=json.dumps({'session_uuid':self.session_uuid})).json()['active_uuid']

    @property
    def data(self):
        if self._nodedata_and_uuid is None or self._nodedata_and_uuid[1] != self.active_uuid:
            node_dict = {key:pd.DataFrame(val) for key, val in requests.post(self.uri(base='active')).json().items()}
            if len(node_dict) == 1:
                nodedata = node_dict.values()[0]
            else:
                nodedata = node_dict
            self._nodedata_and_uuid = nodedata, self.active_uuid

        return self._nodedata_and_uuid[0]



    @property
    def help(self):
        print 'HALP' # TODO: rework CLI argparse to print meaningful help




if __name__ == "__main__":

    c = Cursor(session_uuid='dev')
    c.upload(pd.DataFrame({'a':[1,2], 's':[4,5]}))


    # c.query('area=="VISpm"')
    # c.keep(['area', 'dsi_dg', 'osi_dg', 'g_dsi_dg',]).reload()
    # c.groupby('area')
    


 