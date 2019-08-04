import random
import re

import local_settings as settings


class MarkovChainer(object):
    def __init__(self, order):
        self.order = order
        self.beginnings = []
        self.freq = {}
        self.text_bank = set()

    # pass a string with a terminator to the function to add it to the markov lists.
    def add_sentence(self, string, terminator):
        self.text_bank.add(string)
        data = "".join(string)
        words = data.split()
        buf = []
        if len(words) > self.order:
            words.append(terminator)
            self.beginnings.append(words[0:self.order])
        else:
            pass

        for word in words:
            buf.append(word)
            if len(buf) == self.order + 1:
                mykey = (buf[0], buf[-2])
                if mykey in self.freq:
                    self.freq[mykey].append(buf[-1])
                else:
                    self.freq[mykey] = [buf[-1]]
                buf.pop(0)
            else:
                continue
        return

    def add_text(self, text):
        text = re.sub(r'\n\s*\n/m', ".", text)
        seps = '([.!?;:])'
        pieces = re.split(seps, text)
        sentence = ""
        for piece in pieces:
            if piece != "":
                if re.search(seps, piece):
                    self.add_sentence(sentence, piece)
                    sentence = ""
                else:
                    sentence = piece

    # Generate the goofy sentences that become your tweet.
    def _generate_sentence(self):
        res = random.choice(self.beginnings)
        res = res[:]
        if len(res) == self.order:
            nw = True
            while nw is not None:
                restup = (res[-2], res[-1])
                try:
                    nw = self._next_word_for(restup)
                    if nw is not None:
                        res.append(nw)
                    else:
                        continue
                except Exception:
                    nw = False
            new_res = res[0:-2]
            if new_res[0].istitle() or new_res[0].isupper():
                pass
            else:
                new_res[0] = new_res[0].capitalize()
            sentence = ""
            for word in new_res:
                sentence += word + " "
            sentence += res[-2] + ("" if res[-1] in ".!?;:" else " ") + res[-1]

        else:
            sentence = None
        if sentence is not None:
            if random.randint(0, 8) is 1 and settings.TWEET_AT_CREATOR and settings.CREATOR_USER_NAME:
                sentence += f' @{settings.CREATOR_USER_NAME}'
        return sentence

    def _next_word_for(self, words):
        try:
            arr = self.freq[words]
            next_words = random.choice(arr)
            return next_words
        except Exception:
            return None

    def _get_formatted_text(self):
        for x in range(0, 10):
            ebook_status = self._generate_sentence()
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
                newer_status = self._generate_sentence()
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

    def _check_similarity(self, post_text):
        """
        :param post_text: The text to check
        :return: True if the text is not too similar, False if match found in source_statuses
        """
        if post_text is not None and len(post_text) < 210:
            for status in self.text_bank:
                if post_text[:-1] not in status:
                    continue
                else:
                    return False
        return True

    def new_phrase(self):
        tmp_txt = self._get_formatted_text()
        is_valid = self._check_similarity(post_text=tmp_txt)
        if not is_valid:
            for _ in range(4):
                tmp_txt = self._get_formatted_text()
                is_valid = self._check_similarity(post_text=tmp_txt)

        if not is_valid:
            print('No fitting phrase available')
            return (False, )
        else:
            return (True, tmp_txt, )


if __name__ == "__main__":
    print("Try running ebooks.py first")
