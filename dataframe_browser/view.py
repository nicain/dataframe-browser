from utilities import create_class_logger, one, generate_uuid, BeautifulSoup
import dataframe_browser as dfb
import requests
import json


class ConsoleView(object):

    def __init__(self, **kwargs):
        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']

    


    def display_branch_info(self):
        print '\nBookmarked groups: ("*" means currently active)'
        for name in self.app.model.bookmarks:
            print '{name}{active} ({num_df})'.format(name=name, active='*' if name == self.app.model.active.name else '', num_df=len(self.app.model.get_node_by_name(name)))


    def display_node_info(self, node):

        print '\nGroup info: ({anon} if group not bookmarked)'.format(anon=dfb.ANON_DEFAULT)

        print node

    def display_active(self):
        pass

class FlaskView(ConsoleView):

    def display_active(self):
        self.display_node(self.app.model.active)

    def display_node(self, node, page_length=None):


        if self.app.model.active is None or len(self.app.model.active) < 1:
            response = requests.post('http://localhost:5000/multi', json=json.dumps([]))

        else:
            if page_length is None:
                page_length = 5 if len(self.app.model.active) > 1 else 20

            uuid_table_list = []
            for ni, node in enumerate(self.app.model.active.node_frames):

                if self.app.model.active.name is None:
                    active_name = dfb.ANON_DEFAULT
                else:
                    if len(self.app.model.active) > 1:
                        active_name = '{active_name}[{ni}]'.format(active_name=self.app.model.active_name, ni=ni)
                    else:
                        active_name = self.app.model.active.name
                common_col_list = self.app.model.common_active_columns
                table_html = node.to_html(columns=common_col_list + [c for c in node.columns if c not in common_col_list])
                table_html_bs = BeautifulSoup(table_html).table
                table_uuid = generate_uuid()
                table_html_bs['id'] = table_uuid
                uuid_table_list.append((table_uuid, str(table_html_bs), page_length, active_name))

            response = requests.post('http://localhost:5000/multi', json=json.dumps(uuid_table_list))
        self.logger.info(json.dumps({'DISPLAY_ACTIVE':{'response':str(response)}}, indent=4))


