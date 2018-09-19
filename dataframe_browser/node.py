from nodeframe import NodeFrame
import dataframe_browser as dfb
from utilities import one
from collections import OrderedDict as OD

class Node(object):

    def __init__(self, nodeframes, name=None, parent=None, force=True, keys=None):
        assert isinstance(nodeframes, tuple)

        self._name = name
        for x in nodeframes:
            assert isinstance(x, NodeFrame)

        self._node_frames = nodeframes
        self._parent = parent
        self._children = []

        if keys is None:
            self._key_dict = {ii:nodeframe for ii, nodeframe in zip(range(len(self.node_frames)), self.node_frames)}
        else:
            assert len(keys) == len(nodeframes)
            self._key_dict = {key:nodeframe for key, nodeframe in zip(keys, self.node_frames)}


        if self.parent is None:
            assert self.name == 'root'
        else:
            assert isinstance(self.parent, Node)
            self.parent._children.append(self)
    
    def __getitem__(self, key):
        return self._key_dict[key]

    def get_key(self, cf):
        for key, curr_f in self._key_dict.items():
            if curr_f == cf:
                return key
        raise

    @property
    def name(self):
        return self._name

    @property
    def node_frames(self):
        return self._node_frames

    @property
    def parent(self):
        return self._parent

    def rename(self, new_name):
        self._name = new_name

    @property
    def children(self):
        return self._children

    def items(self):
        return OD((x.name,OD(x.items())) for x in self._children)

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
            describe_df_list = [(self.get_key(x), x.describe(include='all')) for x in self.node_frames]
            for curr_key, df in describe_df_list:
                df.columns.name = '{name_prefix}[{ii}]'.format(name_prefix=name_prefix, ii=curr_key)
            zipped_row_list = zip(*[str(x[1]).split('\n') for x in describe_df_list])
            return '\n'.join(['  |  '.join(row) for row in zipped_row_list])

    def groupby(self, **kwargs):

        new_nodes = []
        for ni, node_frame in enumerate(self.node_frames):
            df_dict, load_time = node_frame.groupby(**kwargs)
            
            key_list, nodeframe_list = [], []
            for key, df in df_dict.items():
                key_list.append(key)
                nodeframe_list.append(NodeFrame(df=df, load_time=load_time))
            
            if self.name is not None:
                # Probably a  index-instead of key bug here too:
                curr_node = Node(tuple(nodeframe_list), name='{parent_name}[{index}]'.format(parent_name=self.name, index=ni), parent=self, force=False, keys=key_list)
            else:
                curr_node = Node(tuple(nodeframe_list), name=None, parent=self, force=False)

            new_nodes.append(curr_node)

        return new_nodes

    def merge(self, **kwargs):

        total_time = 0
        left_node_frame = self.node_frames[0]
        for right_node_frame in self.node_frames[1:]:
            df, load_time = left_node_frame.merge(right_node_frame, **kwargs)
            total_time += load_time
            left_node_frame = NodeFrame(df=df, load_time=total_time)

        return Node((left_node_frame,), name=None, parent=self, force=False)

    def query(self, **kwargs):

        new_nodes = []
        for ni, node_frame in enumerate(self.node_frames):
            df, load_time = node_frame.query(**kwargs)
            
            node_frame = NodeFrame(df=df, load_time=load_time)

            new_node = Node((node_frame,), name=None, parent=self, force=False)
            new_nodes.append(new_node)

        return new_nodes

    def apply(self, **kwargs):

        new_nodes = []
        for node_frame in self.node_frames:
            df, load_time = node_frame.apply(**kwargs)
            node_frame = NodeFrame(df=df, load_time=load_time)
            new_node = Node((node_frame,), name=None, parent=self, force=False)
            new_nodes.append(new_node)

        return new_nodes
            
    def to_graph_dict(self):
        children = [x.to_graph_dict() for x in self.children]
        if len(children) > 0:
            return {'name':str(self.name), 'children':[x.to_graph_dict() for x in self.children]}
        else: 
            return {'name':str(self.name)}

