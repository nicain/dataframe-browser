from utilities import create_class_logger, one, generate_uuid, BeautifulSoup
import dataframe_browser as dfb
import requests
import json
from collections import OrderedDict as OD
import asciitree
import json



class ConsoleView(object):

    def __init__(self, **kwargs):
        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']

    
    def display_message(self, msg, type=None):
        print msg

    def display_branch_info(self):
        print '\nBookmarked groups: ("*" means currently active)'
        for name in self.app.model.bookmarks:
            print '{name}{active} ({num_df})'.format(name=name, active='*' if name == self.app.model.active.name else '', num_df=len(self.app.model.get_node_by_name(name)))


    def display_node_info(self, node):

        print '\nGroup info: ({anon} if group not bookmarked)'.format(anon='')

        print node

    def display_active(self):
        pass

    def display_tree(self):


        root = self.app.model.root
        print asciitree.LeftAligned()({root:OD(root.items())})

class FlaskViewServer(ConsoleView):

    def display_node(self, page_length=None):
    

        if self.app.model.active is None or len(self.app.model.active) < 1:
            uuid_table_list = []

        else:
            if page_length is None:
                page_length = 5 if len(self.app.model.active) > 1 else 20

            uuid_table_list = []
            for frame in self.app.model.active.node_frames:

                # common_col_list = self.app.model.common_active_columns
                # print common_col_list, [c for c in frame.columns if c not in common_col_list]
                # print frame.columns
                table_html = frame.to_html()#columns=common_col_list + [str(c) for c in frame.columns if c not in common_col_list])
                table_html_bs = BeautifulSoup(table_html).table
                table_uuid = generate_uuid()
                table_html_bs['id'] = table_uuid
                uuid_table_list.append((table_uuid, str(table_html_bs), page_length))


        self.logger.info(json.dumps(['DISPLAY_NODE'], indent=4))
        return uuid_table_list

# class FlaskViewClient(ConsoleView):

#     def __init__(self, **kwargs):
        
#         self.port = kwargs.pop('port', 5000)
#         self.uri_base = kwargs.pop('uri_base','localhost')
        
#         super(FlaskViewClient, self).__init__(**kwargs)

#         self.POST_ROUTE ='http://{uri_base}:{port}/model'.format(port=self.port, uri_base=self.uri_base) 
#         self.POST_ROUTE_GRAPH ='http://{uri_base}:{port}/graph'.format(port=self.port, uri_base=self.uri_base)
#         self.POST_RELOAD ='http://{uri_base}:{port}/reload'.format(port=self.port, uri_base=self.uri_base)

#     def display_active(self):
#         self.display_node()
#         response = requests.post(self.POST_RELOAD, json=json.dumps([]))
#         self.display_tree()

#     def display_node(self, page_length=None):
#         # response = requests.post(self.POST_ROUTE, json=json.dumps(uuid_table_list))
#         raise NotImplementedError


#     def display_tree(self):
    
#         super(FlaskViewClient, self).display_tree()

#         root = self.app.model.root
#         response = requests.post(self.POST_ROUTE_GRAPH, json=json.dumps(root.to_graph_dict()))