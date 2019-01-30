import random
import re
import sys
import typing
from datetime import datetime, timedelta

import markov
import twitter
from bs4 import BeautifulSoup
from local_settings import *
from mastodon import Mastodon

try:
    # Python 3
    from html.entities import name2codepoint as n2c
    from urllib.request import urlopen
except ImportError:
    # Python 2
    from htmlentitydefs import name2codepoint as n2c
    from urllib2 import urlopen
    chr = unichr

#TODO add logging
def connect(type='twitter'):
    if type == 'twitter':
        return twitter.Api(consumer_key=MY_CONSUMER_KEY,
                       consumer_secret=MY_CONSUMER_SECRET,
                       access_token_key=MY_ACCESS_TOKEN_KEY,
                       access_token_secret=MY_ACCESS_TOKEN_SECRET,
                       tweet_mode='extended')
    elif type == 'mastodon':
        return Mastodon(client_id=CLIENT_CRED_FILENAME, api_base_url=MASTODON_API_BASE_URL, access_token=USER_ACCESS_FILENAME)
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
    text = re.sub(r'(\#|@|(h\/t)|(http))\S+', '', text)  # Take out URLs, hashtags, hts, etc.
    text = re.sub('\s+', ' ', text)  # collaspse consecutive whitespace to single spaces.
    text = re.sub(r'\"|\(|\)', '', text)  # take out quotes.
    text = re.sub(r'\s+\(?(via|says)\s@\w+\)?', '', text)  # remove attribution
    text = re.sub(r'<[^>]*>','', text) #strip out html tags from mastodon posts
    htmlsents = re.findall(r'&\w+;', text)
    for item in htmlsents:
        text = text.replace(item, entity(item))
    text = re.sub(r'\xe9', 'e', text)  # take out accented e
    return text


def scrape_page(src_url, web_context, web_attributes):
    tweets = []
    last_url = ""
    for i in range(len(src_url)):
        if src_url[i] != last_url:
            last_url = src_url[i]
            print(">>> Scraping {0}".format(src_url[i]))
            try:
                page = urlopen(src_url[i])
            except Exception:
                last_url = "ERROR"
                import traceback
                print(">>> Error scraping {0}:".format(src_url[i]))
                print(traceback.format_exc())
                continue
            soup = BeautifulSoup(page, 'html.parser')
        hits = soup.find_all(web_context[i], attrs=web_attributes[i])
        if not hits:
            print(">>> No results found!")
            continue
        else:
            errors = 0
            for hit in hits:
                try:
                    tweet = str(hit.text).strip()
                except (UnicodeEncodeError, UnicodeDecodeError):
                    errors += 1
                    continue
                if tweet:
                    tweets.append(tweet)
            if errors > 0:
                print(">>> We had trouble reading {} result{}.".format(errors, "s" if errors > 1 else ""))
    return(tweets)


def grab_tweets(api, user_name, max_id=None):
    source_tweets = []
    user_tweets = api.GetUserTimeline(screen_name=user_name, count=200, max_id=max_id, include_rts=True, trim_user=True, exclude_replies=True)
    if user_tweets:
        max_id = user_tweets[-1].id - 1
        for tweet in user_tweets:
            if tweet.full_text:
                tweet.text = filter_status(tweet.full_text)
            else:
                tweet.text = filter_status(tweet.full_text)
            if re.search(SOURCE_EXCLUDE, tweet.text):
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
        print("Error fetching tweets from Twitter. Aborting.")
        sys.exit()
    return twitter_tweets


def grab_mentions(api):
    mentions = api.GetMentions(count=3, trim_user=True)
    return mentions


def reply_to_mention(api, reply_to_id, message):
    if DEBUG:
        print('Debug is on so not sending')
    else:
        print(f'Debug is off, so sending message.')
        api.PostUpdate(status=message, in_reply_to_status_id=reply_to_id, verify_status_length=True, auto_populate_reply_metadata=True)


def handle_mentions(api, chainer, source_statuses): #TODO refactor to not need source_statuses
    mentions = grab_mentions(api=api)

    # Generate replies
    for mention in mentions:
        reply_to_id = mention.id
        mention_text = mention.full_text
        post_time = parse_time(mention.created_at)
        if datetime.now() - post_time > timedelta(hours=4):  # not in past 3 hour and the mention isn't the bot itself:
            continue
        else:
            tmp_msg = get_formatted_text(chainer)
            if check_similarity(tmp_msg, source_statuses):
                if (not DEBUG) and REPLY_TO_MENTIONS:
                    reply_to_mention(api, message=tmp_msg, reply_to_id=reply_to_id)
                print(f'replying to {mention_text} with "{tmp_msg}"')

    # Reply back to people
    # for reply in reply_to_mentions()

def get_formatted_text(markov_chainer):
    for x in range(0, 10):
        ebook_status = markov_chainer.generate_sentence()
    # randomly drop the last word, as Horse_ebooks appears to do.
    if random.randint(0, 4) == 0 and re.search(r'(in|to|from|for|with|by|our|of|your|around|under|beyond)\s\w+$',
                                               ebook_status) is not None:
        print("Losing last word randomly")
        ebook_status = re.sub(r'\s\w+.$', '', ebook_status)
        print(ebook_status)

    # if a tweet is very short, this will randomly add a second sentence to it.
    if ebook_status is not None and len(ebook_status) < 40:
        rando = random.randint(0, 10)
        if rando == 0 or rando == 7:
            print("Short tweet. Adding another sentence randomly")
            newer_status = markov_chainer.generate_sentence()
            if newer_status is not None:
                ebook_status += " " + newer_status
            else:
                ebook_status = ebook_status
        elif rando == 1:
            # say something crazy/prophetic in all caps
            print("ALL THE THINGS")
            ebook_status = ebook_status.upper()
        # throw out tweets that match anything from the source account.

    return ebook_status


def check_similarity(post_text, source_statuses:[str]):
    """

    :param post_text: The text to check
    :param source_statuses: List of strings to check against
    :return: True if the text is not too similar, False if match found in source_statuses
    """
    if post_text is not None and len(post_text) < 210:
        for status in source_statuses:
            if post_text[:-1] not in status:
                continue
            else:
                print("TOO SIMILAR: " + post_text)
                return False
    return True


def grab_toots(api, account_id=None, max_id=None):
    if account_id:
        source_toots = []
        user_toots = api.account_statuses(account_id)
        max_id = user_toots[len(user_toots)-1]['id']-1
        for toot in user_toots:
            if toot['in_reply_to_id'] or toot['reblog']:
                pass #skip this one
            else:
                toot['content'] = filter_status(toot['content'])
                if len(toot['content']) != 0:
                    source_toots.append(toot['content'])
        return source_toots, max_id



def parse_time(string_time):
    day_of_week, month, month_day, time_str, _, year_str = string_time.split(' ')
    month_map = {
        'january': 1,
        'february': 2,
        'march': 3,
        'april': 4,
        'may': 5,
        'june': 6,
        'july': 7,
        'august': 8,
        'september': 9,
        'october': 10,
        'november': 11,
        'december': 12
    }
    month = month.lower()
    month_num = 0
    for key in month_map.keys():
        if month.lower() in key:
            month_num = month_map[key]
            break
    month_day_int = int(month_day)
    hour_str, minute_str, second_str = time_str.split(':')

    kwargs = {
        'month': month_num,
        'day': month_day_int,
        'hour': int(hour_str),
        'minute': int(minute_str),
        'second': int(second_str),
        'year': int(year_str),
    }
    d = datetime(**kwargs)
    return d

def run_all():
    order = ORDER
    guess = 0
    if ODDS and not DEBUG:
        guess = random.randint(0, ODDS - 1)

    if guess:
        print(f"{guess} No, sorry, not this time.")  # message if the random number fails.
        return
    else:
        api = connect()
        source_statuses = []
        if STATIC_TEST:
            file = TEST_SOURCE
            print(">>> Generating from {0}".format(file))
            string_list = open(file).readlines()
            for item in string_list:
                source_statuses += item.split(",")
        if SCRAPE_URL:
            source_statuses += scrape_page(SRC_URL, WEB_CONTEXT, WEB_ATTRIBUTES)
        if ENABLE_TWITTER_SOURCES and TWITTER_SOURCE_ACCOUNTS and len(TWITTER_SOURCE_ACCOUNTS[0]) > 0:
            for handle in TWITTER_SOURCE_ACCOUNTS:
                    source_statuses += get_all_user_tweets(api=api, user_handle=handle)
        if ENABLE_MASTODON_SOURCES and len(MASTODON_SOURCE_ACCOUNTS) > 0:
            source_toots = []
            mastoapi = connect(type='mastodon')
            max_id=None
            for handle in MASTODON_SOURCE_ACCOUNTS:
                accounts = mastoapi.account_search(handle)
                if len(accounts) != 1:
                    pass # Ambiguous search
                else:
                    account_id = accounts[0]['id']
                    num_toots = accounts[0]['statuses_count']
                    if num_toots < 3200:
                        my_range = int((num_toots/200)+1)
                    else:
                        my_range = 17
                    for x in range(my_range)[1:]:
                        source_toots_iter, max_id = grab_toots(mastoapi,account_id, max_id=max_id)
                        source_toots += source_toots_iter
                    print("{0} toots found from {1}".format(len(source_toots), handle))
                    if len(source_toots) == 0:
                        print("Error fetching toots for %s. Aborting." % handle)
                        sys.exit()
            source_statuses += source_toots
        if len(source_statuses) == 0:
            print("No statuses found!")
            sys.exit()
        mine = markov.MarkovChainer(order)
        for status in source_statuses:
            if not re.search('([\.\!\?\"\']$)', status):
                status += "."
            mine.add_text(status)

        formatted_post = get_formatted_text(markov_chainer=mine)
        if REPLY_TO_MENTIONS:
            handle_mentions(api, chainer=mine, source_statuses=source_statuses)
        if check_similarity(formatted_post, source_statuses):
            if not DEBUG:
                if ENABLE_TWITTER_POSTING:
                    status = api.PostUpdate(formatted_post)
                if ENABLE_MASTODON_POSTING:
                    status = mastoapi.toot(formatted_post)


            print(formatted_post)
        else:
            print("Too similar")
            sys.exit()
        if not formatted_post:
            print("Status is empty, sorry.")
        elif len(formatted_post) > 210:
            print("TOO LONG: " + formatted_post)


if __name__ == "__main__":
    run_all()
