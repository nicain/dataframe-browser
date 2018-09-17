from node import Node
from utilities import create_class_logger, one
import json

class Model(object):
    
    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        
        self.app = kwargs['app']
        self._root = Node(tuple(), name='root')
        self._active = self.root

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
            for child in cur_node.get_children():
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

    def set_active(self, name=None, key=None):
        self.logger.info(json.dumps({'SET_ACTIVE':str(name)}, indent=4))
        containing_node = self.get_node_by_name(name)

        if key is not None:
            node_frame, new_key = containing_node[key], '{name}[{key}]'.format(name=name, key=key)

            if new_key in self.bookmarks:
                self._active = self.get_node_by_name(new_key)
            else:
                new_node = self.app.controller.create_node((node_frame,), parent=containing_node, name=new_key, force=False)
                self.app.model.set_active(new_key)

        else:
            self._active = containing_node

        self.app.view.display_active()

    @property
    def common_active_columns(self):
        return sorted(set.intersection(*[set(node.columns) for node in self.active.node_frames]))

    @property
    def all_active_columns(self):
        return sorted(set.union(*[set(node.columns) for node in self.active.node_frames]))



        
