"""Improve admission policy; never change scores, models, or variant ordering."""
import re
import unicodedata



def has_new_wording(original, candidate):
    """A revision must change words, not just whitespace, case or punctuation."""
    def words(text):
        return re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold())
    return isinstance(candidate, str) and bool(words(candidate)) and words(original) != words(candidate)
