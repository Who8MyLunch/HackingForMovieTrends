
from __future__ import division, print_function, unicode_literals

import re
import os
import fnmatch

import requests_oauthlib
import oauthlib
import yaml_io

try:
    from htmlentitydefs import name2codepoint
except ImportError:
    # Must be Python 3.x
    from html.entities import name2codepoint
    unichr = chr


def unescaper(match):
    """Custom un-escape function.

    """
    name2codepoint_work = name2codepoint.copy()
    name2codepoint_work['apos']=ord("'")

    code = match.group(1)
    if code:
        return unichr(int(code, 10))
    else:
        code = match.group(2)
        if code:
            return unichr(int(code, 16))
        else:
            code = match.group(3)
            if code in name2codepoint_work:
                return unichr(name2codepoint_work[code])

    return match.group(0)


def decode(s, encoding='utf-8'):
    """Decode string entity.

    """
    EntityPattern = re.compile(u'&(?:#(\d+)|(?:#x([\da-fA-F]+))|([a-zA-Z]+));')
    result = EntityPattern.sub(unescaper, s.decode(encoding))

    return result


def extract_url(text):
    result = re.search("(?P<url>https?://[^\s]+)", text)
    if result:
        url = result.group("url")
    else:
        url = None

    return url


#####################################################

def file_finder(paths_search, file_patterns='*'):
    """An iterator that yields files matching a pattern.

    Parameters
    ----------
    paths_search : a string or a sequence of strings.
    file_patterns : a string or a sequence of strings.

    Useage
    ------
        finder = file_finder('/usr/local', '*.c')
        for f in finder:
            print(f)
    """

    if isinstance(paths_search, basestring):
        paths_search = [paths_search]

    if isinstance(file_patterns, basestring):
        file_patterns = [file_patterns]

    # Loop over base paths for recursive search.
    for path_work in paths_search:
        path_work = os.path.normpath(path_work)

        # Iterate over found files and folders.
        for root, dirnames, filenames in os.walk(path_work):
            local_matches = []
            for fp in file_patterns:
                for f in fnmatch.filter(filenames, fp):
                    local_matches.append(os.path.join(root, f))

            # Yield found matches to caller.
            for f in local_matches:
                yield os.path.normpath(f)


def authenticate(fname_api='twitter_api.yml'):
    """Generate a requests.Session object authorized via OAuth-2.

    Twitter API urls:
     - url_api = 'https://api.twitter.com'
     - url_request_oauth1_token = url_api + '/oauth/request_token'
     - url_request_oauth2_token = url_api + '/oauth2/token'
     - url_authorize = url_api + '/oauth/authorize'
     - url_access_token = url_api + '/oauth/access_token'
    """
    # Load application's Twitter API details.
    info_twitter = yaml_io.read(fname_api)

    client_key = info_twitter['consumer_key']
    # client_secret = info_twitter['consumer_secret']
    access_token = info_twitter['access_token']

    # Backend client / desktop client application workflow.
    client = oauthlib.oauth2.BackendApplicationClient(client_key)
    token = {'access_token': access_token, 'token_type': 'Bearer'}

    # Generate requests.Session object.
    session = requests_oauthlib.OAuth2Session(client, token=token)

    return session


def rate_limit_from_api(session, resources='search'):
    """Query Twitter API for current rate limit status.
    """
    url_status = 'https://api.twitter.com/1.1/application/rate_limit_status.json'
    params = {'resources': resources}

    # Request information from Twitter.
    response = session.get(url_status, params=params)

    # Interpret the results.
    info_status = response.json()

    try:
        info_search = info_status['resources']['search']['/search/tweets']
    except KeyError:
        code = info_status['errors'][0]['code']
        if code == 88:
            message = info_status['errors'][0]['message']
            raise ValueError(message)
        else:
            raise

    limit = info_search['limit']
    remaining = info_search['remaining']
    reset = info_search['reset']

    info = {'limit': limit, 'remaining': remaining, 'reset': reset}

    return info


def rate_limit_from_header(hdr):
    """Parse rate limit information from response header.
    """
    try:
        limit = hdr['x-rate-limit-limit']
        remaining = hdr['x-rate-limit-remaining']
        reset = hdr['x-rate-limit-reset']

        info = {'limit': limit, 'remaining': remaining, 'reset': reset}
    except KeyError:
        info = None

    return info


if __name__ == '__main__':
    pass
