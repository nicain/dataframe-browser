import argparse
from dataframe_browser.dataframebrowser import DataFrameBrowser
import logging
import os

parser = argparse.ArgumentParser(description='Pandas dataframe browser cli', prog='dataframe-browser')
parser.add_argument("--clean-exit", action='store_false', help='Do not exit to python at the end', dest='not_clean_exit')
parser.add_argument("--non-interactive", action='store_true', help='Exit after commands are envoked', dest='non_interactive')
parser.add_argument('commands', nargs='*', type=str, help='Commands to envoke')

dataframe_browser = DataFrameBrowser(logging_settings={'level':logging.INFO, 'handler':logging.StreamHandler()})

def main():
    
    args = parser.parse_args()

    input = [''.join(args.commands)]

    if args.not_clean_exit:
        os.environ["PYTHONINSPECT"] = 'i'
        dataframe_browser.run(input=input, interactive=not args.non_interactive)
        print 'Output stored in "dataframe_browser"'
    
    else:
        dataframe_browser.run(input=input, interactive=not args.non_interactive)


    

if __name__ == '__main__':
    main()