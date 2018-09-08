import pandas as pd
import sys
import traceback
from collections import OrderedDict
import asciitree

prompt = '>>>'

class Node(object):

    def __init__(self, df, metadata=None, parent=None, quiet_init=False):
        self.df = df
        self.children = OrderedDict()
        self.parent = parent
        self.metadata = metadata
        self.active = True
        if not quiet_init:
            self.print_df(head=False)

    def push(self, *args, **kwargs):
        kwargs['parent'] = self
        new_node = Node(*args, **kwargs)
        self.children[new_node] = new_node
        self.active = False
        return new_node

    def print_df(self, head=True):
        if head == True:
            tmp = self.df.head()
        else:
            tmp = self.df
        print tmp

    def __str__(self):
        if self.active:
            return str(self.metadata) + ': ACTIVE'
        else:
            return str(self.metadata)

    def items(self):
        return self.children.items()


    def print_tree(self):
        curr_node = self
        while curr_node.parent is not None:
            curr_node = curr_node.parent
        root_node = curr_node

        if root_node.active == True:
            print asciitree.LeftAligned()({'{0}: ACTIVE'.format(str(root_node.metadata)):root_node.children})
        else:
            print asciitree.LeftAligned()({str(root_node.metadata):root_node.children})



help_val = 'h'
quit_val = 'exit'
select_val = 'q'
escape_val = 'x'
print_val = 'p'
print_val_upper = print_val.upper()
print_tree = 'T'
parent_val = '{'
child_val = '}'
next_sibling_val = '>'
previous_sibling_val = '<'

navigation_val_list = [parent_val, child_val, next_sibling_val, previous_sibling_val]



all_help_vals = OrderedDict([
                  (select_val,'query'),
                  (escape_val,'escape/cancel'),
                  (print_val,'print DataFrame.head()'),
                  (print_val_upper,'print DataFrame'),
                  (print_tree,'print DataFrame Tree'),
                  (help_val,'print help'),
                  (quit_val,'exit'),
                ])

def parse_navigation(result, curr_node):

    def set_new_node(old_node, new_node):
        old_node.active = False
        new_node.active = True
        return new_node

    if result == parent_val:
        if curr_node.parent is None:
            print 'Root DataFrame has no parent'
            return curr_node
        else:
            return set_new_node(curr_node, curr_node.parent)
    elif result == child_val:
        if len(curr_node.children) == 0:
            print 'Current DataFrame has no children' 
            return curr_node
        else:
            return set_new_node(curr_node, curr_node.children.values()[0])
    elif result == next_sibling_val:
        if curr_node.parent is None:
            print 'Root DataFrame has no siblings'
            return curr_node
        sibling_list = curr_node.parent.children.values()
        curr_index = sibling_list.index(curr_node)
        if curr_index == len(sibling_list) - 1:
            return set_new_node(curr_node, sibling_list[0])
        else:
            return set_new_node(curr_node, sibling_list[curr_index+1])
    elif result == previous_sibling_val:
        if curr_node.parent is None:
            print 'Root DataFrame has no siblings'
            return curr_node
        sibling_list = curr_node.parent.children.values()
        curr_index = sibling_list.index(curr_node)
        return set_new_node(curr_node, sibling_list[curr_index-1])
    else:
        raise RuntimeError


def print_help(help_menu):
    for key, val in help_menu.items():
        print '[{0:1}]: {1:10}'.format(key, val)

select_help_options = [quit_val, help_val, escape_val, print_val, print_val_upper, print_tree]
select_help_menu = OrderedDict((key, all_help_vals[key]) for key in select_help_options)
def select(curr_node, query=None):

    while True:
        if query is None:
            result = raw_input('>q> ')
        else:
            result = query

        if result == quit_val:
            sys.exit()
        elif result == help_val:
            print_help(select_help_menu)
        elif result == escape_val:
            return
        elif result == print_val:
            curr_node.print_df(head=True)
        elif result == print_val_upper:
            curr_node.print_df(head=False)
        else:

            new_df = None
            try:
                if result.strip() in curr_node.df.columns:
                    new_df = curr_node.df[[result.strip()]]
                    return curr_node.push(new_df, metadata=('select', result))
                else:
                    new_df = curr_node.df.query(result)
                    return curr_node.push(new_df, metadata=('query', result))
            except:
                print traceback.print_exc()
                query = raw_input('>q> ')
                continue
            
            print '  Invalid option; please enter one of: {0} (h for help)'.format('/'.join(select_help_options))
            continue



general_help_options = [select_val, print_val_upper, print_val, print_tree, help_val, quit_val]
general_help_menu = OrderedDict((key,all_help_vals[key]) for key in general_help_options)
def main(curr_node):
    
    
    print 
    print_help(general_help_menu)
    while True:
    
        result = raw_input('{0} '.format(prompt))
        
        if result == quit_val:
            sys.exit()
        elif result == help_val:
            print_help(general_help_menu)
            continue
        elif result == select_val:
            return_val = select(curr_node)
            curr_node = return_val if not return_val is None else curr_node
        elif len(result) > 0 and result[0] == select_val and result[1] == ':':
            return_val = select(curr_node, query=result[2:])
            curr_node = return_val if not return_val is None else curr_node

        elif result == print_val:
            curr_node.print_df(head=True)
            continue
        elif result == print_val_upper:
            curr_node.print_df(head=False)
            continue
        elif result == print_tree:
            curr_node.print_tree()
            continue
        elif result in navigation_val_list:
            curr_node = parse_navigation(result, curr_node)
        elif len(result) == 0:
            curr_node.print_df(head=False)
            continue
        else:
            print '  Invalid option; please enter one of: {0} (h for help)'.format('/'.join(general_help_options))



if __name__ == '__main__':

    df = pd.DataFrame({'a':[1,2,3,1,2,2,2], 'b':[.1,.2,.3,.4, .5,.4,.1], 'c':['a', 'b', 'c', 'b', 'a', 'a', 'b']})
    curr_node = Node(df, metadata='example')
    main(curr_node)