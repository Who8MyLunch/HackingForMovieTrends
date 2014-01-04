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

import numpy as np
import requests
import arrow
import BeautifulSoup

import yaml_io
import json_io

import utilities
import errors

#################################################


def id_from_name(name):
    name = os.path.basename(name)

    b, e = os.path.splitext(name)
    parts = b.split('_')
    id_str = parts[2]

    return int(id_str)


def timestamp_from_name(fname):
    tw = Tweet.from_file(fname)

    return tw.timestamp


def filter(tweet):
    """Test if supplied Tweet is acceptable (i.e. not SPAM).

    More ideas:
     - Direct Message?
     - Following disproportionate, compared to number following them.

    """
    # Individual tests for undesirable tweet.
    flag_source = not tweet.source == 'unknown'
    flag_url = not tweet.has_url
    flag_retweet = not tweet.retweet

    # Tweet is OK if all tests pass.
    flag_ok = flag_source and flag_url and flag_retweet

    return flag_ok

#################################################


class Tweet(object):

    pattern = 'tw_????-??-??_*.json'

    def __init__(self, json):
        self._json = json
        self._id = int(self._json['id_str'])

    def __repr__(self):
        """A nicely-formatted representation of Tweet's internal JSON data.
        """
        t = 'Tweet Object:\n'
        s = json_io.pretty(self._json)
        return t + s

    @property
    def has_url(self):
        return len(self._json['entities']['urls']) > 0

    @property
    def url(self):
        if self.has_url:
            return self._json['entities']['urls'][0]['expanded_url']
        else:
            return None

    @property
    def url_title(self):
        """Return title of first URL page, if URL exists.
        """
        if self.has_url:
            resp = requests.get(self.url)
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
        src = self._json['source']

        # Parse HTML for app type.
        apps = ['web', 'txt', 'iphone', 'android', 'blackberry']
        for a in apps:
            if a in src.lower():
                return a

        # Source not specified in above list.
        return 'unknown'

    @property
    def source_full(self):
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
        If present, a tuple in the form (longitude, latitude),
        otherwise, None.
        """
        return self._json['coordinates']

    @property
    def name(self):
        """Unique name for this Tweet, suitable for use as a file name.  Does not include
        the extension and does not include full path.
        """
        fname = 'tw_{:d}-{:02d}-{:02d}_{:d}'.format(self.timestamp.year,
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
            os.makedirs(path)

        fname = os.path.join(path, self.name + '.json')
        json_io.write(fname, self._json)

        return fname

    @staticmethod
    def from_file(fname):
        """Instantiate a Tweet object from previously-serialized Tweet object.
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
    def __init__(self, path_base=None, warn_repeat=False):
        # self._query = query

        self._min_id = np.inf
        self._max_id = 0

        self.warn_repeat = warn_repeat

        if not path_base:
            path_base = os.path.abspath(os.path.curdir)

        self._path = path_base

        if not os.path.isdir(self._path):
            os.makedirs(self._path)

        # Dict of all managed Tweets.  Mapping from Tweet ID to full path file name.
        self._id_toc = {}
        self._id_ordered = []

        # Dict of cached Tweets.  Mapping from Tweet ID to Tweet object.
        # self._cache = {}

        # Find Tweets.
        self.scan_files()

    @property
    def path(self):
        """Top-level folder containing Tweets and/or folders with more Tweets.
        """
        return self._path

    def scan_files(self):
        """Scan file system, reference all found Tweets.  Return Tweet count.
        """
        self._count = 0
        self._id_toc = {}
        self._id_ordered = []

        finder = utilities.file_finder(self.path, Tweet.pattern)
        for f in finder:
            self.add_tweet_file(f, do_sort=False)

        # Sort the IDs now that we're done.
        self._id_ordered.sort()

        return self.count

    def add_tweet_file(self, tw_f, do_sort=True):
        """Add Tweet file to collection.
        """
        if not os.path.isfile(tw_f):
            raise IOError('Input file does not exist: {:s}'.format(tw_f))

        id_int = id_from_name(tw_f)

        if id_int in self._id_toc:
            if self.warn_repeat:
                raise errors.TwitterError('Repeated tweet: {:s}'.format(tw_f))
            else:
                # Quietly handle the issue.  Don't add the Tweet.
                return self.count

        self._id_toc[id_int] = tw_f
        self._id_ordered.append(id_int)

        self._count += 1
        self.update_min_max_id(id_int)

        if do_sort:
            self._id_ordered.sort()

        return self.count

    def add_tweet_obj(self, tw_o):
        """Add Tweet object to collection.  Save to file.
        """
        if not isinstance(tw_o, Tweet):
            raise errors.TwitterError('Input object must be of type Tweet')

        folder = '{:d}-{:02d}-{:02d}'.format(tw_o.timestamp.year,
                                             tw_o.timestamp.month,
                                             tw_o.timestamp.day)

        path_save = os.path.join(self.path, folder)

        tw_f = tw_o.serialize(path_save)
        self.add_tweet_file(tw_f)

        return self.count

    @property
    def count(self):
        """Number of Tweets in this collection.
        """
        return self._count

    def update_min_max_id(self, id_int):
        if id_int < self._min_id:
            self._min_id = id_int

        if id_int > self._max_id:
            self._max_id = id_int

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

        f = self._id_toc[self.min_id]
        return timestamp_from_name(f)

    @property
    def max_timestamp(self):
        if not self.count:
            return None

        f = self._id_toc[self.max_id]
        return timestamp_from_name(f)

    @property
    def ids(self):
        """Sequence of all ordered IDs.
        """
        return self._id_ordered

    def tweet_from_id(self, tweet_id):
        """Return Tweet object for corresponding Tweet ID.
        """
        id_int = int(tweet_id)
        f = self._id_toc[id_int]

        tw = Tweet.from_file(f)

        return tw

    @property
    def tweets(self):
        """Iterator (generator) over all Tweets, sorted by ID.
        """
        for id_int in self._id_ordered:
            yield self.tweet_from_id(id_int)

#################################################


class Search_Manager(Tweet_Manager):
    """Add search capability on top of Tweet_Manager class.
    """

    # Type of search to be fetched from Twitter API.
    _result_type = 'recent'  # 'recent' | 'popular' | 'mixed'

    def __init__(self, session, query, path_base=None, warn_repeat=False):
        """Instantiate a new Search_Manager object.
        """

        folder_query = query.lower().replace(' ', '_')
        path_query = os.path.join(path_base, folder_query)

        super(Search_Manager, self).__init__(path_base=path_query, warn_repeat=warn_repeat)

        # Requests.session object.
        self._session = session

        self._query = query

        # Search results generator.
        self._searcher = Search(self._session)

    @property
    def query(self):
        return self._query

    @property
    def api_limit(self):
        return self._searcher.api_limit

    @property
    def api_remaining(self):
        return self._searcher.api_remaining

    @property
    def api_seconds(self):
        return self._searcher.api_seconds

    @property
    def api_minutes(self):
        return self._searcher.api_minutes

    def search_continuous(self):
        """Keep searching...
        """
        keep_looping = True
        while keep_looping:
            print('\nCount: {:d}'.format(self.count))

            try:
                ok_api = self.search(refresh=True)

                # Check if hit API limit.
                if ok_api:
                    # Search ended without hitting API limit.
                    print('Search ended.')
                    keep_looping = False
                else:
                    if self.api_remaining > 1:
                        # Probably not a rate-limit problem.  Just wait a short bit.
                        dt = 30.  # seconds.

                        print('Network something what??')
                        print('Seconds: {:f}'.format(self.api_seconds))
                        print('Remaining: {:d}'.format(self.api_remaining))
                    else:
                        # Probably hit API limit.  Wait until timeout expires, then try again.
                        dt = self.api_seconds

                        print('API rate limit')
                        print('Seconds: {:f}'.format(self.api_seconds))
                        print('Remaining: {:d}'.format(self.api_remaining))

                    if dt < 0:
                        dt = 0.

                    # Minutes and seconds.
                    m = int(dt / 60.)
                    s = dt - m * 60

                    print('Waiting: {:2d}:{:02}'.format(m, s))

                    print('Count: {:d}'.format(self.count))

                    time.sleep(dt)

            except KeyboardInterrupt:
                # Exit main loop.
                print('User interupt!')
                keep_looping = False

    def search(self, refresh=True):
        """Search for tweets.
        """
        try:
            # Search for older Tweets.  Automatically continue where left off previously.
            gen = self._searcher.run(self.query,
                                     max_id=self.min_id - 1,
                                     result_type=self._result_type)
            for tw in gen:
                self.add_tweet_obj(tw)

            # Search for new tweets since last search.
            gen = self._searcher.run(self.query,
                                     since_id=self.max_id,
                                     result_type=self._result_type)
            for tw in gen:
                self.add_tweet_obj(tw)

        except errors.APILimitError:
            return False

        except errors.NetworkError:
            return False

        return True

#################################################


class Search(object):
    def __init__(self, session):
        """Twitter Search API helper class.

        Parameters
        ----------
        session : requests.Session object authorized via OAuth-2.
        """

        # http://stackoverflow.com/questions/4028904/how-to-get-the-home-directory-in-python
        path_config = os.path.join(os.path.expanduser('~'), '.tweet_finder')
        if not os.path.isdir(path_config):
            os.mkdir(path_config)

        self.fname_config = os.path.join(path_config, 'config.yml')

        count = 100  # requested "tweets per page"

        self.session = session
        self.count = count

        self.url_search = 'https://api.twitter.com/1.1/search/tweets.json'

        self._limit = None
        self._remaining = None
        self._reset = None

        self.load_config()
        self.initialize_rate_limits()

    def run(self, query, since_id=0, max_id=np.inf, result_type='recent', lang='en'):
        """Generator yielding individual tweets matching supplied query string.

        Parameters
        ----------
        query : str, Twitter search query, e.g. "python is nice".
        since_id : int
        max_id : int
        result_type : str, 'mixed', 'recent', 'popular'
        """

        self.initialize_rate_limits()

        time_pause = 0.1

        # Main loop over requests to Twitter API endpoint.
        while True:
            if since_id > 0 and max_id < np.inf:
                if since_id >= max_id:
                    msg = 'Invalid ID values: {:d} vs {:d}'.format(since_id, max_id)
                    raise errors.TwitterError(msg)

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
            try:
                response = self.session.get(self.url_search, params=params)
            except requests.ConnectionError as e:
                raise errors.NetworkError(e)

            self.update_rate_limits(response.headers)

            # Interpret the search results.
            info_search = response.json()

            # Yield individual tweets.  Raise StopIteration if no more tweets.
            try:
                tweets = info_search['statuses']
            except KeyError:
                msg = info_search['errors'][0]['message']
                self._remaining = 0
                self.save_config()

                raise errors.APILimitError('API limit exceeded: {:s}'.format(msg))

            if len(tweets) == 0:
                # No results returned.  All done for now.
                raise StopIteration

            # Loop over returned tweets, yield them to caller.
            for json in tweets:
                tw = Tweet(json)

                if tw.id_int < max_id:
                    max_id = tw.id_int - 1

                yield tw

            # A little pause between requests.
            time.sleep(time_pause)

    def load_config(self):
        try:
            info = yaml_io.read(self.fname_config)
        except IOError:
            info = None

        if info:
            self._limit = int(info['limit'])
            self._remaining = int(info['remaining'])
            self._reset = int(info['reset'])
        else:
            # Set safe default values.
            self._limit = 15 * 60
            self._remaining = 0
            self._reset = None

    def save_config(self):
        info = {'limit': int(self._limit),
                'remaining': int(self._remaining),
                'reset': int(self._reset)}

        yaml_io.write(self.fname_config, info)

    def initialize_rate_limits(self):
        """Initialize limit values via rate-limit API call.
        """
        try:
            info = utilities.rate_limit_from_api(self.session)

            self._limit = int(info['limit'])
            self._remaining = int(info['remaining'])
            self._reset = int(info['reset'])

            self.save_config()
        except Exception as e:  # test for appropriate error type here.
            print(e)
            raise

    def update_rate_limits(self, hdr):
        """Update API rate limits from just-received response header.
        """
        info = utilities.rate_limit_from_header(hdr)

        self._limit = int(info['limit'])
        self._remaining = int(info['remaining'])
        self._reset = int(info['reset'])

        self.save_config()

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
        seconds_max = 15. * 60.  # 15 minutes max.

        reset = arrow.get(self._reset)
        delta = reset - arrow.now()
        seconds = delta.total_seconds()

        if seconds > seconds_max:
            seconds = seconds_max

        if seconds < 0:
            # Uhhh... how did we get here?
            # It's Ok.  Just means we have stale information.  It will get updated very shortly.
            # raise errors.WierdError
            pass

        return seconds

    @property
    def api_minutes(self):
        """Minutes to wait before API limit is automatically reset.
        """
        return self.api_seconds / 60.
