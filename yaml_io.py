from __future__ import division, print_function, unicode_literals

import os
import yaml


def read(fname, *args, **kwargs):
    b, e = os.path.splitext(fname)
    fname = b + '.yml'

    return yaml.load(open(fname), *args, **kwargs)


def write(fname, data, *args, **kwargs):
    b, e = os.path.splitext(fname)
    fname = b + '.yml'

    with open(fname, 'w') as fo:
        yaml.safe_dump(data, stream=fo, width=50, indent=4, default_flow_style=False, **kwargs)
