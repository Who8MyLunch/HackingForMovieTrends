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

import numpy as np

import json_io
import yaml_io

import utilities

import requests
import requests_oauthlib
import oauthlib

import arrow


# Load application's Twitter API details.
fname_twitter_api = 'twitter_api.yml'
info_twitter = yaml_io.read(fname_twitter_api)

client_id = info_twitter['consumer_key']
client_secret = info_twitter['consumer_secret']
access_token = info_twitter['access_token']

# Twitter API urls.
# url_api = 'https://api.twitter.com'
# url_request_oauth1_token = url_api + '/oauth/request_token'
# url_request_oauth2_token = url_api + '/oauth2/token'
# url_authorize = url_api + '/oauth/authorize'
# url_access_token = url_api + '/oauth/access_token'

# Backend client.
client = oauthlib.oauth2.BackendApplicationClient(client_id)

# Generate a requests.Session object authorized via OAuth-2.
token = {'access_token': access_token, 'token_type': 'Bearer'}
twitter = requests_oauthlib.OAuth2Session(client, token=token)


def twitter_status():
    """Query Twitter API for current rate limit status.

    """
    url_status = 'https://api.twitter.com/1.1/application/rate_limit_status.json'
    params = {'resources': 'search'}

    # Request information from Twitter.
    response = twitter.get(url_status, params=params)

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

    delta = arrow.get(info_search['reset']) - arrow.now()
    minutes = delta.total_seconds()/60.

    limit = info_search['limit']
    remaining = info_search['remaining']

    info = {'limit': limit, 'remaining': remaining, 'minutes': minutes}

    return info



def searcher(twitter_session, query, count=100, lang='en', **kwargs):
    """Generator yielding individual tweets matching supplied query string.

    Parameters
    ----------
    twitter_session : requests.Session object authorized via OAuth-2.
    query : str, Twitter search query, e.g. "python is nice".
    count : int, maximum number of tweets to return per "page".  Default is 100.

    """
    # Setup.
    url_search = 'https://api.twitter.com/1.1/search/tweets.json'
    current_min_id = np.inf

    while True:
        # Check API status.
        status = twitter_status()
        print(status)

        if not status['remaining']:
            raise ValueError('No API queries remain in current time interval.  Please wait {:.2f} minutes.'.format(status['minutes']))

        params = {'q': query, 'count': count, 'lang': lang, 'include_entities': True}
        if current_min_id < np.inf:
            params['max_id'] = current_min_id

        # Request information from Twitter.
        response = twitter_session.get(url_search, params=params)

        # Interpret the results.
        info_search = response.json()

        metadata = info_search['search_metadata']
        print(metadata)

        tweets = info_search['statuses']
        if len(tweets) == 0:
            raise StopIteration

        for json in tweets:
            tw = Tweet(json)

            if tw.id < current_min_id:
                current_min_id = tw.id

            yield tw

        # Get ready to make another API call.
        since_id = int(metadata['max_id_str'])
        print('b', since_id)




class Tweet(object):
    def __init__(self, json):
        self.json = json

    @property
    def has_url(self):
        return self.json['entities']['urls']

    @property
    def url_title(self):
        """Return title of first URL page, if URL exists.
        """

        if self.has_url:
            # Grab the first URL.
            url =  self.json['entities']['urls'][0]['expanded_url']

            resp = requests.get(url)
            soup = BeautifulSoup.BeautifulSoup(resp.content)
            results = soup.title.string
        else:
            results = None

        return results

    @property
    def is_retweet(self):
        """Indicate if this tweet is a retweet.
        https://dev.twitter.com/docs/platform-objects/tweets
        """
        return 'retweeted_status' in self.json

    @property
    def text(self):
        results = self.json['text']

        # Check to see if there any URLs embedded in text.
        if self.json['entities']['urls']:
            # Grab the first URL, crop all URLs from text.
            ixs = self.json['entities']['urls'][0]['indices']
            results = results[:ixs[0]]

        return results

    @property
    def id(self):
        """Twitter tweet ID.
        """
        return  int(self.json['id_str'])

    @property
    def timestamp(self):
        """Time when Tweet was created.

        e.g. Sat Dec 28 16:56:41 +0000 2013'
        """

        format = 'ddd MMM DD HH:mm:ss Z YYYY'
        stamp = arrow.get(self.json['created_at'], format)

        return stamp


    def to_file(self, fname):
        """Serialize this Tweet to a JSON file.
        """
        b, e = os.path.splitext(fname)
        fname = b + '.json'

        json_io.write(fname, self.json)


    @staticmethod
    def from_file(fname):
        """Instanciate a Tweet object from previously-serialized Tweet.
        """
        b, e = os.path.splitext(fname)
        fname = b + '.json'

        json = json_io.read(fname)

        tw = Tweet(json)
        return tw

#######################################################################

