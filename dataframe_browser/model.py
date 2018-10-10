from node import Node
from utilities import create_class_logger, one
import json

class Model(object):
    
    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        
        self.app = kwargs['app']
        self._root = Node(tuple()) # Not build with create_node
        self._active = self.root

        self.groupable_max_unique = 250

    @property
    def active(self):
        return self._active

    @property
    def root(self):
        return self._root

    @property
    def nodes(self):

        nodes = []
        stack = [self.root]
        while stack:
            cur_node = stack[0]
            stack = stack[1:]
            nodes.append(cur_node)
            for child in cur_node.children:
                stack.append(child)
        
        return nodes
    
    @property
    def bookmarks(self):
        return [n.name for n in self.nodes if n.name is not None]

    def get_filtered_node_list(self, filter_fcn):
        return [n for n in self.nodes if filter_fcn(n)]

    def get_node_by_name(self, bookmark):
        node_list = self.get_filtered_node_list(lambda n: n.name == bookmark)
        if len(node_list) == 0:
            return None
        else:
            return one(node_list)

    def set_active(self, node, name=None, key=None):

        self.logger.info(json.dumps({'SET_ACTIVE':str(name)}, indent=4))

        if key is not None:
            if name is None:
                containing_node = self.active
                node_frame = containing_node[key]
                new_node = self.app.controller.create_node((node_frame,), parent=containing_node)
                self.app.model.set_active(new_node)
            else:
                containing_node = self.get_node_by_name(name)
                new_key = '{name}[{key}]'.format(name=name, key=key)

                if new_key in self.bookmarks:
                    self._active = self.get_node_by_name(new_key)

                else:
                    node_frame = containing_node[key]
                    new_node = self.app.controller.create_node((node_frame,), parent=containing_node, name=new_key, force=False)
                    self.app.model.set_active(new_node, name=new_key)

            


        else:
            self._active = node

        self.app.view.display_active()

    @property
    def common_active_columns(self):
        L = [set([str(x) for x in node_frame.columns]) for node_frame in self.active.node_frames]
        if len(L) == 0:
            return []
        else:
            return sorted(set.intersection(*L))

    @property
    def all_active_columns(self):
        return self.active.all_columns

    @property
    def active_is_root(self):
        return self.active == self.root

    @property
    def active_is_leaf(self):
        return len(self.active.children) == 0

    @property
    def active_is_bookmarked(self):
        return not self.active.name is None

    @property
    def number_of_active_frames(self):
        return len(self.active.node_frames)

    @property
    def groupable_state(self):
        if self.number_of_active_frames == 1 and self.foldable_state:
            return True
        else:
            return False

    @property
    def foldable_state(self):
        if len(self.groupable_columns_dict) > 0:
            return True
        else:
            return False


    @property
    def groupable_columns_dict(self):
        return_dict = {}

        if len(self.active.node_frames) == 0:
            return return_dict

        for c in self.active.node_frames[0].df.columns:
            try:
                n_unique = len(self.active.node_frames[0].df[c].unique())
                if n_unique < self.groupable_max_unique:
                    return_dict[c] = n_unique
            except TypeError:
                pass
        return return_dict
    
    @property
    def can_concatenate(self):
        if self.number_of_active_frames > 1:
            return True
        else:
            return False

    @property
    def all_index_columns(self):

        L = [set([str(x) for x in node_frame.index_cols]) for node_frame in self.active.node_frames]
        if len(L) == 0:
            return []
        else:
            return list(set.intersection(*L))
