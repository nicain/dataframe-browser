import requests
import pgpasslib
import json


class Cursor(object):

    def __init__(self, port=5000, hostname='localhost'):

        self.port = port
        self.hostname = hostname
    
    @property
    def command(self):
        return 'http://{hostname}:{port}/command'.format(hostname=self.hostname, port=self.port)

    def run(self, **kwargs):
        print kwargs
        result = requests.post(self.command, json=json.dumps(kwargs))
        if result.status_code != 200:
            result.raise_for_status()
        return self

    def open(self, filename=None, reload=False):
        return self.run(command='open', filename=filename, reload=reload)

    def read(self, query=None, uri=None, reload=False):
        return self.run(command='read', query=query, uri=uri, reload=reload)

    def query(self, query=None, reload=False):
        return self.run(command='query', query=query, reload=reload)

    def groupby(self, by=None, reload=False):
        return self.run(command='groupby', by=by, reload=reload)

    def groupfold(self, by=None, reload=False):
        return self.run(command='groupfold', by=by, reload=reload)

    def drop(self, columns=None, frames=None, reload=False):
        return self.run(command='drop', columns=columns, reload=reload, frames=frames)

    def keep(self, columns=None, frames=None, reload=False):
        return self.run(command='keep', columns=columns, frames=frames, reload=reload)

    def concat(self, how='vertical', reload=False):
        return self.run(command='concat', how=how, reload=reload)
    
    def apply(self, column=None, mapper=None, new_column=None, lazy=True, reload=False, drop=False):
        return self.run(command='apply', column=column, mapper=mapper, new_column=new_column, lazy=lazy, reload=reload, drop=drop)

    def reload(self):
        return self.run(command='reload', reload=True)
    
    def back(self, N=1, reload=False):
        return self.run(command='back', N=N, reload=reload)

    def forward(self, reload=False):
        return self.run(command='forward', reload=reload)

    def bookmark(self, name=None, reload=False):
        return self.run(command='bookmark', name=name, reload=reload)


    @property
    def help(self):
        print 'HALP' # TODO: rework CLI argparse to print meaningful help




if __name__ == "__main__":

    c = Cursor()

    c.open(filename='/home/nicholasc/projects/dataframe-browser/data/cell_specimens.p')
    c.query('area=="VISpm"')
    c.keep(['area', 'dsi_dg', 'osi_dg', 'g_dsi_dg',]).reload()
    # c.groupby('area')
    


 