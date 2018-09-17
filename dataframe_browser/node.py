from nodeframe import NodeFrame
import dataframe_browser as dfb
from utilities import one

class Node(object):

    def __init__(self, nodeframes, name=None, parent=None, force=True):
        assert isinstance(nodeframes, tuple)

        self._name = name
        for x in nodeframes:
            assert isinstance(x, NodeFrame)

        self._node_frames = nodeframes
        self._parent = parent
        self._children = []

        if self.parent is None:
            assert self.name == 'root'
        else:
            assert isinstance(self.parent, Node)
            self.parent._children.append(self)
    


    @property
    def name(self):
        return self._name

    @property
    def node_frames(self):
        return self._node_frames

    @property
    def parent(self):
        return self._parent

    def get_children(self):
        return self._children

    def __len__(self):
        return len(self.node_frames)


    def __str__(self):

        if self.name is None:
            name_prefix = '<anon>'.format(anon=dfb.ANON_DEFAULT)
        else:
            name_prefix = self.name

        if len(self) == 1:
            describe_df = one(self.node_frames).describe(include='all')
            describe_df.columns.name = '{name_prefix}'.format(name_prefix=name_prefix)
            return str(describe_df)
        else:
            describe_df_list = [x.describe(include='all') for x in self.node_frames]
            for ii, df in enumerate(describe_df_list):
                df.columns.name = '{name_prefix}[{ii}]'.format(name_prefix=name_prefix, ii=ii)
            zipped_row_list = zip(*[str(x).split('\n') for x in describe_df_list])
            return '\n'.join(['  |  '.join(row) for row in zipped_row_list])