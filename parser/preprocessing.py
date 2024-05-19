import re
import nltk
import re
import string
import nltk
import pymorphy3
from nltk.corpus import stopwords


class Preprocessing:
    def __init__(self) -> None:
        self.spec_chars = string.punctuation + r'\n\x0«»\t—…[]\n*'
        self.stop_words = stopwords.words('russian')
        self.morph = pymorphy3.MorphAnalyzer()

    def preprocess(self, text):
        text = "".join([ch for ch in text if ch not in self.spec_chars])
        text = re.sub('\n', '     ', text)
        tokens = nltk.word_tokenize(text)
        filtered_text = [word.lower() for word in tokens if word.lower() not in self.stop_words]
        final_text = []

        for word in filtered_text:
            if word.isalpha() and len(word) > 2:
                p = self.morph.parse(word)[0]
                final_text.append(p.normal_form)
            else:
                continue

        return final_text