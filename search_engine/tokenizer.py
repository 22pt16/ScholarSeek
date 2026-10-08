import re
from typing import List

# Comprehensive list of common English stop words
DEFAULT_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves"
}

def simple_stem(word: str) -> str:
    """
    Lightweight rule-based stemmer to reduce words to root form.
    Handles common suffixes like -ing, -ed, -es, -s, -ly, -ment, -tion.
    """
    word = word.lower()
    if len(word) <= 3:
        return word

    if word.endswith("ing") and len(word) > 5:
        return word[:-3]
    if word.endswith("edly") and len(word) > 6:
        return word[:-4]
    if word.endswith("es") and len(word) > 4:
        return word[:-2]
    if word.endswith("ed") and len(word) > 4:
        return word[:-2]
    if word.endswith("ly") and len(word) > 4:
        return word[:-2]
    if word.endswith("ment") and len(word) > 6:
        return word[:-4]
    if word.endswith("tions") and len(word) > 6:
        return word[:-5] + "tion"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
        
    return word


class Tokenizer:
    def __init__(self, stop_words: set = None, enable_stemming: bool = True):
        self.stop_words = stop_words if stop_words is not None else DEFAULT_STOP_WORDS
        self.enable_stemming = enable_stemming

    def tokenize(self, text: str) -> List[str]:
        """
        Converts text into normalized, filtered, and stemmed tokens.
        """
        if not text:
            return []

        # Convert to lower case and find all alphanumeric tokens
        raw_tokens = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())

        tokens = []
        for token in raw_tokens:
            # Skip stop words and purely numeric short codes if desired
            if token in self.stop_words:
                continue

            if self.enable_stemming:
                stemmed = simple_stem(token)
                tokens.append(stemmed)
            else:
                tokens.append(token)

        return tokens

    def tokenize_with_positions(self, text: str):
        """
        Returns list of (token, position) tuples for phrase search & positional indexing.
        """
        if not text:
            return []

        matches = re.finditer(r'\b[a-zA-Z0-9]+\b', text.lower())
        results = []
        pos = 0

        for match in matches:
            raw_token = match.group(0)
            if raw_token not in self.stop_words:
                token = simple_stem(raw_token) if self.enable_stemming else raw_token
                results.append((token, pos, match.start(), match.end()))
            pos += 1

        return results
