from nodeframe import NodeFrame
import dataframe_browser as dfb
from utilities import one
from collections import OrderedDict as OD
import pandas as pd

class Node(object):

    def __init__(self, nodeframes, name=None, parent=None, force=True, keys=None):
        assert isinstance(nodeframes, tuple)

        self._name = name
        for x in nodeframes:
            assert isinstance(x, NodeFrame)

        self._node_frames = nodeframes
        self._parent = parent
        self._children = []
        self._child_set_from_back_button = None

        if keys is None:
            self._key_dict = {ii:nodeframe for ii, nodeframe in zip(range(len(self.node_frames)), self.node_frames)}
        else:
            assert len(keys) == len(nodeframes)
            self._key_dict = {key:nodeframe for key, nodeframe in zip(keys, self.node_frames)}


        if self.parent is None:
            assert self.name is None
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
            name_prefix = '<anon>'.format(anon='')
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
            
            curr_node = Node(tuple(nodeframe_list), name=None, parent=self, force=False) # Not built using create node
            new_nodes.append(curr_node)

        return new_nodes

    def groupfold(self, by=None):
    
        node_frame_list = []
        for _, node_frame in enumerate(self.node_frames):
            df, load_time = node_frame.pivot(by=by)
            node_frame = NodeFrame(df=df, load_time=load_time)
            node_frame_list.append(node_frame)
        new_node = Node(tuple(node_frame_list), name=None, parent=self, force=False)

        return new_node

    def drop(self, columns=None, frames=None):

        if frames is None:
            frames_to_drop = []
        else:
            frames_to_drop = [int(ii) for ii in frames]
        
        node_frame_list = []
        for frame_index, node_frame in enumerate(self.node_frames):
            if frame_index not in frames_to_drop:
                df, load_time = node_frame.drop(columns=columns)
                node_frame = NodeFrame(df=df, load_time=load_time)
                node_frame_list.append(node_frame)
        new_node = Node(tuple(node_frame_list), name=None, parent=self, force=False)

        return new_node

    def keep(self, columns=None, frames=None):

        if frames is None:
            frames_to_keep = range(len(self.node_frames))
        else:
            frames_to_keep = [int(ii) for ii in frames]
        
        node_frame_list = []
        for frame_index, node_frame in enumerate(self.node_frames):
            if frame_index in frames_to_keep:
                df, load_time = node_frame.keep(columns=columns)
                node_frame = NodeFrame(df=df, load_time=load_time)
                node_frame_list.append(node_frame)
        new_node = Node(tuple(node_frame_list), name=None, parent=self, force=False)

        return new_node

    def concat(self, how='vertical'):
        
        if how == 'vertical':
            axis=1
        elif how == 'horizontal':
            axis=0
        else: 
            raise RuntimeError

        df_list = []
        for _, node_frame in enumerate(self.node_frames):
            df_list.append(node_frame.df)
        new_df = pd.concat(df_list)
        node_frame = NodeFrame(df=new_df, load_time=None)
        new_node = Node((node_frame,), name=None, parent=self, force=False)

        return new_node


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

