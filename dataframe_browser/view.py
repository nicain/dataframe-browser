from utilities import create_class_logger, one
import dataframe_browser as dfb


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



