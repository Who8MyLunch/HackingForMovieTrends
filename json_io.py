
from __future__ import division, print_function, unicode_literals

import numpy as np
import simplejson as json

#
# Helpers.
#
MARKER = ':ndar!'


class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            name = '%s.%s' % (MARKER, obj.dtype.name)
            encoded_obj = {name: obj.tolist()}
        else:
            encoded_obj = json.JSONEncoder.default(self, obj)

        # Done.
        return encoded_obj


def numpy_hook(decoded_obj):
    if isinstance(decoded_obj, dict):
        if len(decoded_obj) == 1:
            key, val = decoded_obj.items()[0]

            if MARKER in key:
                dtype_name = key[len(MARKER) + 1:]
                decoded_obj = np.asarray(val, dtype=dtype_name)
    # Done.
    return decoded_obj

#################################################


def read(fname):
    """Read serialized data from JSON file, decode into Python object(s).

    Parameters
    ----------
    fname : string file name.

    """
    # Read string from JSON file.
    with open(fname, 'r') as fi:
        serial = fi.read()

    # Decode.
    decoder = json.JSONDecoder(object_hook=numpy_hook)
    data = decoder.decode(serial)

    return data


def write(fname, data):
    """Encode Python object(s), write to JSON file.

    Parameters
    ----------
    fname : string file name.
    data : Data to be written to file.  May include Numpy arrays.

    """
    # Encode to string.
    encoder = NumpyJSONEncoder(check_circular=True, indent='  ')
    serial = encoder.encode(data)

    # Write to file.
    with open(fname, 'w') as fo:
        fo.write(serial)


def pretty(data_dict):
    s = json.dumps(data_dict, sort_keys=True, indent=4, separators=(',', ': '))
    return s
