from node import Node
from utilities import create_class_logger, one
import json

class Model(object):
    
    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        
        self.app = kwargs['app']
        self._root = Node(tuple()) # Not build with create_node
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
            for child in cur_node.children:
                stack.append(child)
        
        return nodes

    @property
    def bookmarked_nodes(self):
        return [n for n in self.nodes if n.name is not None]

    @property
    def bookmark_dict(self):
        return {n.name:n for n in self.nodes}

    @property
    def bookmarks(self):
        return [n.name for n in self.bookmarked_nodes]

    

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
    def active_is_bookmarked(self):
        if self.active is None:
            return False
        return not self.active.name is None

    @property
    def session_uuid(self):
        return self.app.session_uuid