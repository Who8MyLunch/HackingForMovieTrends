#!/usr/bin/python

from __future__ import division, print_function, unicode_literals

import os

import twitter
import utilities

import yaml_io
import docopt


def main():
    """
    ---------------------
    Twitter Search Update
    ---------------------

    Usage:
        pdate.py <fname_config> [options]

    Options:
        -z             Enable Z-profile in second window
        -h --help      Show this help message.

    """

    # Parse command line arguments.
    args = docopt.docopt(main.__doc__)

    # Load data from file.
    fname = args['<fname_config>']

    info = yaml_io.read(fname)

    print(info['queries'])
    session = utilities.authenticate()

    path_query = os.path.join(os.path.curdir, 'tweets')

    manager = twitter.Search_Manager(session, query, path_query)

    print('\nStatus')
    print('------')
    print('client_id:  {:s}'.format(session.client_id.client_id))
    print('Limit:      {:d}'.format(manager.api_limit))
    print('Remaining:  {:d}'.format(manager.api_remaining))
    print('Minutes:  {:5.2f}'.format(manager.api_minutes))

    print()
    print('Count: {:d}'.format(manager.count))

    manager.search_continuous()

    print('\nStatus')
    print('------')
    print('client_id:  {:s}'.format(session.client_id.client_id))
    print('Limit:      {:d}'.format(manager.api_limit))
    print('Remaining:  {:d}'.format(manager.api_remaining))
    print('Minutes:  {:5.2f}'.format(manager.api_minutes))

    print()
    print('Count: {:d}'.format(manager.count))

    # Done.

if __name__ == '__main__':
    main()

