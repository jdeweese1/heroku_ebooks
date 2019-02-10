import random
import re
import sys
import scraper
from datetime import datetime, timedelta

import markov
import twitter
import local_settings as settings
from mastodon import Mastodon

import utils

try:
    # Python 3
    from html.entities import name2codepoint as n2c

except ImportError:
    # Python 2
    from htmlentitydefs import name2codepoint as n2c
    chr = unichr

#  TODO add logging


def connect(type='twitter'):
    if type == 'twitter':
        return twitter.Api(consumer_key=settings.MY_CONSUMER_KEY,
                           consumer_secret=settings.MY_CONSUMER_SECRET,
                           access_token_key=settings.MY_ACCESS_TOKEN_KEY,
                           access_token_secret=settings.MY_ACCESS_TOKEN_SECRET,
                           tweet_mode='extended')
    elif type == 'mastodon':
        return Mastodon(client_id=settings.CLIENT_CRED_FILENAME,
                        api_base_url=settings.MASTODON_API_BASE_URL,
                        access_token=settings.USER_ACCESS_FILENAME)
    return None


def entity(text):
    if text[:2] == "&#":
        try:
            if text[:3] == "&#x":
                return chr(int(text[3:-1], 16))
            else:
                return chr(int(text[2:-1]))
        except ValueError:
            pass
    else:
        guess = text[1:-1]
        if guess == "apos":
            guess = "lsquo"
        numero = n2c[guess]
        try:
            text = chr(numero)
        except KeyError:
            pass
    return text


def filter_status(text):
    text = re.sub(r'\b(RT|MT) .+', '', text)  # take out anything after RT or MT
    text = re.sub(r'(\#|@|(h\/t)|(http))\S+', '', text)  # Take out settings.URLs, hashtags, hts, etc.
    text = re.sub('\s+', ' ', text)  # collaspse consecutive whitespace to single spaces.
    text = re.sub(r'\"|\(|\)', '', text)  # take out quotes.
    text = re.sub(r'\s+\(?(via|says)\s@\w+\)?', '', text)  # remove attribution
    text = re.sub(r'<[^>]*>', '', text)  # strip out html tags from mastodon posts
    htmlsents = re.findall(r'&\w+;', text)
    for item in htmlsents:
        text = text.replace(item, entity(item))
    text = re.sub(r'\xe9', 'e', text)  # take out accented e
    return text


def grab_tweets(api, user_name, max_id=None):
    source_tweets = []
    user_tweets = api.GetUserTimeline(
        screen_name=user_name,
        count=200,
        max_id=max_id,
        include_rts=True,
        trim_user=True,
        exclude_replies=True)
    if user_tweets:
        max_id = user_tweets[-1].id - 1
        for tweet in user_tweets:
            if tweet.full_text:
                tweet.text = filter_status(tweet.full_text)
            else:
                tweet.text = filter_status(tweet.full_text)
            if re.search(settings.SOURCE_EXCLUDE, tweet.text):
                continue
            if tweet.text:
                source_tweets.append(tweet.text)
    else:
        pass
    return source_tweets, max_id


def get_all_user_tweets(api, user_handle: str):
    twitter_tweets = []
    handle_stats = api.GetUser(screen_name=user_handle)
    status_count = handle_stats.statuses_count
    max_id = None
    my_range = min(17, int((status_count / 200) + 1))
    for x in range(1, my_range):
        twitter_tweets_iter, max_id = grab_tweets(api, user_name=user_handle, max_id=max_id)
        twitter_tweets += twitter_tweets_iter
    print("{0} tweets found in {1}".format(len(twitter_tweets), user_handle))
    if not twitter_tweets:
        print(f"Error fetching tweets from Twitter for {user_handle}. Aborting.")
    return twitter_tweets


def grab_mentions(api):
    mentions = api.GetMentions(count=3, trim_user=True)
    return mentions


def reply_to_mention(api, reply_to_id, message):
    if settings.DEBUG:
        print(f'Debug is on so not replying with {message}')
    else:
        print(f'Debug is off, so replying with {message}.')
        api.PostUpdate(
            status=message,
            in_reply_to_status_id=reply_to_id,
            verify_status_length=True,
            auto_populate_reply_metadata=True)


def handle_mentions(api, chainer):
    mentions = grab_mentions(api=api)

    # Generate replies
    for mention in mentions:
        reply_to_id = mention.id
        mention_text = mention.full_text
        post_time = utils.parse_time(mention.created_at)
        if datetime.now() - post_time > timedelta(hours=settings.REPLY_INTERVAL):  # not in past x hours
            continue
        else:
            rtn_bool, *other_rtns = chainer.new_phrase()
            if rtn_bool:
                if settings.REPLY_TO_MENTIONS:
                    msg = other_rtns[0]
                    reply_to_mention(api, message=msg, reply_to_id=reply_to_id)


def grab_toots(api, account_id=None, max_id=None):
    if account_id:
        source_toots = []
        user_toots = api.account_statuses(account_id)
        max_id = user_toots[len(user_toots) - 1]['id'] - 1
        for toot in user_toots:
            if toot['in_reply_to_id'] or toot['reblog']:
                pass  # skip this one
            else:
                toot['content'] = filter_status(toot['content'])
                if len(toot['content']) != 0:
                    source_toots.append(toot['content'])
        return source_toots, max_id


def run_all():
    order = settings.ORDER
    guess = 0
    if settings.ODDS and not settings.DEBUG:
        guess = random.randint(0, settings.ODDS - 1)

    if guess is not 0:
        print(f"{guess} No, sorry, not this time.")  # message if the random number fails.
        return
    else:
        api = connect()
        source_statuses = []
        if settings.STATIC_TEST:
            file_name = settings.TEST_SOURCE
            print(">>> Generating from {0}".format(file_name))
            string_list = open(file_name).readlines()
            for item in string_list:
                source_statuses += item.split(",")
        if settings.SCRAPE_URL:
            source_statuses += scraper.scrape_page(settings.SRC_URL, settings.WEB_CONTEXT, settings.WEB_ATTRIBUTES)
        if settings.ENABLE_TWITTER_SOURCES and settings.TWITTER_SOURCE_ACCOUNTS and len(settings.TWITTER_SOURCE_ACCOUNTS[0]) > 0:
            for handle in settings.TWITTER_SOURCE_ACCOUNTS:
                    source_statuses += get_all_user_tweets(api=api, user_handle=handle)
        if settings.ENABLE_MASTODON_SOURCES and len(settings.MASTODON_SOURCE_ACCOUNTS) > 0:
            source_toots = []
            mastoapi = connect(type='mastodon')
            max_id = None
            for handle in settings.MASTODON_SOURCE_ACCOUNTS:
                accounts = mastoapi.account_search(handle)
                if len(accounts) != 1:
                    pass  # Ambiguous search
                else:
                    account_id = accounts[0]['id']
                    num_toots = accounts[0]['statuses_count']
                    if num_toots < 3200:
                        my_range = int((num_toots / 200) + 1)
                    else:
                        my_range = 17
                    for _ in range(my_range)[1:]:
                        source_toots_iter, max_id = grab_toots(mastoapi, account_id, max_id=max_id)
                        source_toots += source_toots_iter
                    print("{0} toots found from {1}".format(len(source_toots), handle))
                    if len(source_toots) == 0:
                        print("Error fetching toots for %s. Aborting." % handle)
                        sys.exit()
            source_statuses += source_toots
        if len(source_statuses) == 0:
            print("No statuses found!")
            return
        mine = markov.MarkovChainer(order)
        for status in source_statuses:
            if not re.search('([\.\!\?\"\']$)', status):
                status += "."
            mine.add_text(status)

        if settings.REPLY_TO_MENTIONS:
            handle_mentions(api, chainer=mine)

        rtn_bool, *other_rtns = mine.new_phrase()
        if rtn_bool and other_rtns[0]:
            msg = other_rtns[0]
            if not settings.DEBUG:
                if settings.ENABLE_TWITTER_POSTING:
                    api.PostUpdate(msg)
                if settings.ENABLE_MASTODON_POSTING:
                    mastoapi.toot(msg)
            print(msg)
        if not rtn_bool:
            print("Couldn't generate message")


if __name__ == "__main__":
    run_all()
