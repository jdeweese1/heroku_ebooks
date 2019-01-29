from pathlib import Path

import environ

'''
Local Settings for a heroku_ebooks account. 
'''
root = environ.Path(__file__) - 1
env = environ.Env()

BASE_DIR = Path(root())

READ_DOT_ENV_FILE = env.bool('READ_DOT_ENV_FILE', default=True)
if READ_DOT_ENV_FILE is True:
    environ.Env.read_env(str(BASE_DIR.joinpath('.env')))

# Configuration for Twitter API
ENABLE_TWITTER_SOURCES = env.bool("ENABLE_TWITTER_SOURCES", default=True)  # Fetch twitter statuses as source
ENABLE_TWITTER_POSTING = env.bool("ENABLE_TWITTER_POSTING", default=True)  # Tweet resulting status?
REPLY_TO_MENTIONS = env.bool('REPLY_TO_MENTIONS', default=False)
CREATOR_USER_NAME = env.str("CREATOR_USER_NAME", "")
TWEET_AT_CREATOR = env.str('TWEET_AT_CREATOR', default=False)
MY_CONSUMER_KEY = env('MY_CONSUMER_KEY')  # Your Twitter API Consumer Key set in Heroku config
MY_CONSUMER_SECRET = env('MY_CONSUMER_SECRET')  # Your Consumer Secret Key set in Heroku config
MY_ACCESS_TOKEN_KEY = env('MY_ACCESS_TOKEN_KEY')  # Your Twitter API Access Token Key set in Heroku config
MY_ACCESS_TOKEN_SECRET = env('MY_ACCESS_TOKEN_SECRET')  # Your Access Token Secret set in Heroku config

# Configuration for Mastodon API
ENABLE_MASTODON_SOURCES = env.bool("ENABLE_MASTODON_SOURCES", default=False)  # Fetch mastodon statuses as a source?
ENABLE_MASTODON_POSTING = env.bool("ENABLE_MASTODON_POSTING", default=False)  # Toot resulting status?
MASTODON_API_BASE_URL = ""  # an instance url like https://botsin.space
CLIENT_CRED_FILENAME = ''  # the MASTODON client secret file you created for this project
USER_ACCESS_FILENAME = ''   # The MASTODON user credential file you created at installation.

# Sources (Twitter, Mastodon, local text file or a web page)
TWITTER_SOURCE_ACCOUNTS = env.list('TWITTER_SOURCE_ACCOUNTS', default=['jaroddeweese', 'hotdogsladies', 'zarcasticness', 'GeritWag'])  # A list of comma-separated, quote-enclosed Twitter handles of account that you'll generate tweets based on. It should look like ["account1", "account2"]. If you want just one account, no comma needed.
MASTODON_SOURCE_ACCOUNTS = [""]  # A list, e.g. ["@user@instance.tld"]
SOURCE_EXCLUDE = r'^$'  # Source tweets that match this regexp will not be added to the Markov chain. You might want to filter out inappropriate words for example.

STATIC_TEST = env('STATIC_TEST', default=False)  # Set this to True if you want to test Markov generation from a static file instead of the API.
TEST_SOURCE = env('TEST_SOURCE', default="testcorpus.txt")  # The name of a text file of a string-ified list for testing. To avoid unnecessarily hitting Twitter API. You can use the included testcorpus.txt, if needed.

SCRAPE_URL = env.bool("SCRAPE_URL", default=False)  # Set this to true to scrape a webpage.
SRC_URL = ['http://www.example.com/one', 'https://www.example.com/two']  # A comma-separated list of URLs to scrape
WEB_CONTEXT = ['span', 'h2']  # A comma-separated list of the tag or object to search for in each page above.
WEB_ATTRIBUTES = [{'class': 'example-text'}, {}]  # A list of dictionaries containing the attributes for each page.

ODDS = env.int('ODDS', default=8)  # How often do you want this to run? 1/8 times?
ORDER = 2  # How closely do you want this to hew to sensical? 2 is low and 4 is high.

DEBUG = env('DEBUG', default=True)  # Set this to False to start Tweeting live
TWEET_ACCOUNT = ""  # The name of the account you're tweeting to.

# Configuration for Twitter parser. TEST_SOURCE will be re-used as as the corpus location.
TWITTER_ARCHIVE_NAME = env('TWITTER_ARCHIVE_NAME', default="tweets.csv")  # Name of your twitter archive
IGNORE_RETWEETS = env('IGNORE_RETWEETS', default=True)  # If you want to remove retweets

RUN_INTERVAL = env('RUN_INTERVAL', default=15)  # Time in minutes to run job
