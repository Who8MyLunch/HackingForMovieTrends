from __future__ import division, print_function, unicode_literals

"""
Helper functions for playing with Twitter API.

Twitter OAuth-2
---------------

 - https://dev.twitter.com/docs/auth/application-only-auth
 - https://dev.twitter.com/docs/api/1.1/post/oauth2/token
 - http://requests-oauthlib.readthedocs.org/en/latest/oauth2_workflow.html?highlight=grant-type

"""

import os
import time
import glob

import numpy as np
import requests
import requests_oauthlib
import oauthlib
import arrow
import BeautifulSoup

import json_io
import yaml_io

#################################################


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

    reset = arrow.get(info_search['reset'])
     # - arrow.now()
    # minutes = delta.total_seconds() / 60.

    limit = info_search['limit']
    remaining = info_search['remaining']

    info = {'limit': limit, 'remaining': remaining, 'reset': reset}

    return info


def rate_limit_from_header(hdr):
    """Parse rate limit information from response header.
    """
    limit = hdr['x-rate-limit-limit']
    remaining = hdr['x-rate-limit-remaining']

    reset = arrow.get(hdr['x-rate-limit-reset'])

    info = {'limit': limit, 'remaining': remaining, 'reset': reset}

    return info

#################################################


class Tweet(object):
    def __init__(self, json):
        self._json = json
        self._id = int(self._json['id_str'])

    @property
    def has_url(self):
        return len(self._json['entities']['urls']) > 0

    @property
    def url_title(self):
        """Return title of first URL page, if URL exists.
        """
        if self.has_url:
            # Grab the first URL.
            url = self._json['entities']['urls'][0]['expanded_url']

            resp = requests.get(url)
            soup = BeautifulSoup.BeautifulSoup(resp.content)
            results = soup.title.string
        else:
            results = None

        return results

    @property
    def retweet_count(self):
        """Number of times this tweet has been retweeted.
        Questions: Implies this tweet is the original tweet??
        """
        return self._json['retweet_count']

    @property
    def retweet(self):
        """Indicate if this tweet is a retweet.
        https://dev.twitter.com/docs/platform-objects/tweets
        """
        return 'retweeted_status' in self._json

    @property
    def source(self):
        """Utility used to post the Tweet, as an HTML-formatted string.
        """
        return self._json['source']

    @property
    def text(self):
        """Main text from this Tweet.
        """
        results = self._json['text']

        # Check to see if there any URLs embedded in text.
        if self._json['entities']['urls']:
            # Grab the first URL, crop all URLs from text.
            ixs = self._json['entities']['urls'][0]['indices']
            results = results[:ixs[0]]

        return results

    @property
    def id_int(self):
        """Twitter tweet ID as int64.
        """
        return self._id

    @property
    def id_str(self):
        """Twitter tweet ID as string.
        """
        return self._json['id_str']

    @property
    def timestamp(self):
        """Time when this Tweet was created.
        e.g. Sat Dec 28 16:56:41 +0000 2013'
        """

        fmt = 'ddd MMM DD HH:mm:ss Z YYYY'
        stamp = arrow.get(self._json['created_at'], fmt)

        return stamp

    @property
    def coordinates(self):
        """The longitude and latitude of the Tweet's location.
        A tuple in the form (longitude, latitude).
        """
        return self._json['coordinates']

    @property
    def name(self):
        """Unique name for this tweet, suitable for use as a file name.  Does not include
        the extension and does not include full path.
        """
        fname = 'tw_{:d}-{:02d}-{:02d}_{:d}.json'.format(self.timestamp.year,
                                                         self.timestamp.month,
                                                         self.timestamp.day,
                                                         self.id_int)
        return fname

    def serialize(self, path=None):
        """Serialize this Tweet to a JSON file.
        """
        if not path:
            path = os.path.join(os.path.curdir, 'tweets')

        if not os.path.isdir(path):
            os.mkdir(path)

        fname = os.path.join(path, self.name + '.json')
        json_io.write(fname, self._json)

        return fname

    @staticmethod
    def from_file(fname):
        """Instanciate a Tweet object from previously-serialized Tweet object.

        """
        b, e = os.path.splitext(fname)
        fname = b + '.json'

        if not os.path.isfile(fname):
            raise IOError('File does not exist: {:s}'.format(fname))

        json = json_io.read(fname)
        tw = Tweet(json)

        return tw

#################################################


class Tweet_Manager(object):
    """Manage a collection of Tweets received as a result of performing a query to Twitter's API.
    """
    def __init__(self, query, path_base=None):
        self._query = query

        self._min_id = np.inf
        self._max_id = 0

        # Folder containing managed tweets.
        folder = 'TQ_' + query.replace(' ', '+')
        if not path_base:
            path_base = os.path.abspath(os.path.curdir)

        # Full path to tweets folder.
        self._path_tweets = os.path.join(path_base, folder)
        if not os.path.isdir(self._path_tweets):
            os.mkdir(self._path_tweets)

        # Update min and max ID numbers.
        self.scan_min_max_id()

    @property
    def path_tweets(self):
        return self._path_tweets

    @property
    def query(self):
        return self._query

    @property
    def files(self):
        """Sequence of all Tweets' file names.
        example: fname = 'tw_2013-12-24_415303361420726273.json'
        """
        p = os.path.join(self.path_tweets, 'tw_????-??-??_*.json')
        files = glob.glob(p)
        files = np.sort(files)

        return files

    @property
    def count(self):
        """Number of Tweets in this collection.
        """
        return len(self.files)

    def id_from_name(self, fname):
        b, e = os.path.splitext(fname)
        parts = b.split('_')
        id_str = parts[3]

        return int(id_str)

    def timestamp_from_name(self, fname):
        tw = Tweet.from_file(fname)

        return tw.timestamp

    def update_min_max_id(self, id_int):
        if id_int < self._min_id:
            self._min_id = id_int

        if id_int > self._max_id:
            self._max_id = id_int

    def scan_min_max_id(self):
        for f in self.files:
            id_int = self.id_from_name(f)
            self.update_min_max_id(id_int)

    @property
    def min_id(self):
        return self._min_id

    @property
    def max_id(self):
        return self._max_id

    @property
    def min_timestamp(self):
        if not self.count:
            return None

        f = self.files[0]
        return self.timestamp_from_name(f)

    @property
    def max_timestamp(self):
        if not self.count:
            return None

        f = self.files[-1]
        return self.timestamp_from_name(f)

#################################################


class Search_Manager(Tweet_Manager):
    """Add search capability on top of existing Tweet_Manager.
    """

    # Type of search to be fetched from Twitter API.
    _result_type = 'recent'  # 'recent' | 'popular' | 'mixed'

    def __init__(self, session, query, path_base=None):
        """Instanciate a new Search_Manager object.
        """
        super(Search_Manager, self).__init__(query, path_base=path_base)

        # Requests.session object.
        self._session = session

        # Search results generator.
        self._searcher = Tweet_Search(self._session)

    @property
    def limit(self):
        return self._searcher.limit

    @property
    def remaining(self):
        return self._searcher.remaining

    @property
    def seconds(self):
        return self._searcher.seconds

    def search(self, refresh=True):
        """Search for tweets.  Automatically continue where left off previously.
        """
        gen = self._searcher.run(self.query, max_id=self.min_id - 1, result_type=self._result_type)
        for tw in gen:
            if not tw.has_url:
                tw.serialize(path=self.path_tweets)
                self.update_min_max_id(tw.id_int)

        if refresh:
            self.update()

    def update(self):
        """Search for new tweets since last search.
        """
        gen = self._searcher.run(self.query, since_id=self.max_id, result_type=self._result_type)
        for tw in gen:
            if not tw.has_url:
                tw.serialize(path=self.path_tweets)
                self.update_min_max_id(tw.id_int)

#################################################


class Tweet_Search(object):
    def __init__(self, session):
        """Tweet Search helper.

        Parameters
        ----------
        session : requests.Session object authorized via OAuth-2.
        """
        count = 100  # requested "tweets per page"

        self.session = session
        self.count = count

        self.url_search = 'https://api.twitter.com/1.1/search/tweets.json'

        self._limit = None
        self._remaining = None
        self._reset = None

        self.initialize_rate_limits()

    def run(self, query, since_id=0, max_id=np.inf, result_type='mixed', lang='en'):
        """Generator yielding individual tweets matching supplied query string.

        Parameters
        ----------
        query : str, Twitter search query, e.g. "python is nice".
        since_id : int
        max_id : int
        result_type : str, 'mixed', 'recent', 'popular'
        """
        # Main loop over requests to Twitter API endpoint.
        while True:
            if since_id > 0 and max_id < np.inf:
                if since_id >= max_id:
                    msg = 'Invalid ID values: {:d} vs {:d}'.format(since_id, max_id)
                    raise ValueError(msg)

            params = {'q': query,
                      'count': self.count,
                      'result_type': result_type,
                      'lang': lang,
                      'since_id': since_id,
                      'include_entities': True}

            if max_id < np.inf:
                # Update max_id based on minimum ID of already received OR stored tweets.
                params['max_id'] = max_id

            # Request information from Twitter REST API.
            response = self.session.get(self.url_search, params=params)

            self.update_rate_limits(response.headers)

            # Interpret the search results.
            info_search = response.json()

            # Yield individual tweets.  Raise StopIteration if no more tweets.
            try:
                tweets = info_search['statuses']
            except KeyError:
                raise ValueError(info_search['errors'][0]['message'])

            if len(tweets) == 0:
                # No results returned.
                raise StopIteration

            # Loop over returned tweets.
            for json in tweets:
                tw = Tweet(json)

                if tw.id_int < max_id:
                    max_id = tw.id_int - 1

                yield tw

            # A little pause between requests.  Be nice to Twitter?
            time.sleep(0.1)

    def initialize_rate_limits(self):
        """Inialize rate limits via API call.
        """
        info = rate_limit_from_api(self.session)

        self._limit = info['limit']
        self._remaining = info['remaining']
        self._reset = info['reset']

    def update_rate_limits(self, hdr):
        """Update API rate limits from response header.
        """
        info = rate_limit_from_header(hdr)

        self._limit = info['limit']
        self._remaining = info['remaining']
        self._reset = info['reset']

    @property
    def api_limit(self):
        """API request limit.
        """
        return self._limit

    @property
    def api_remaining(self):
        """API requests remaining.
        """
        return self._remaining

    @property
    def api_seconds(self):
        """Seconds to wait before API limit is automatically reset.
        """
        delta = self._reset - arrow.now()
        seconds = delta.total_seconds()

        return seconds
