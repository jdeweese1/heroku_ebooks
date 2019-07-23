from bs4 import BeautifulSoup

try:
    from urllib.request import urlopen
    import requests
except ImportError:
    from urllib2 import urlopen


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
                print(">>> We had trouble reading {} result{}.".format(
                    errors, "s" if errors > 1 else ""))
    return (tweets)


def scrape_web_text_file(src_url):
    resp = requests.get(src_url)
    if resp.status_code != 200:
        return ''
    return resp.content.decode('utf-8')
