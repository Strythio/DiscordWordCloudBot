from functools import lru_cache
import math
import re
from collections import Counter

WORD = re.compile(r"\w+")

def calc_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator
def cosine_similarity(a, b):
    a_words = WORD.findall(a)
    b_words = WORD.findall(b)
    return calc_cosine(Counter(a_words), Counter(b_words))

@lru_cache(maxsize=None)
def calc_spam_probability(input: str):
    prepared_text = ''.join(c.upper() for c in input if c.isalpha() or c == ' ')
    text_length = len(prepared_text)

    # Two 'windows' of text must be at least this similar to be considered "the same"
    similar_threshold = 0.75
    # The length of the repeats * the number of repeats must be at
    # least this many characters for full confidence in the probability
    # of spam. Any less, and a penalty will be applied
    min_length_for_full_confidence = 75

    spam_probability = 0.0
    # search for a repeating pattern of length `scan_window_size`
    for scan_window_size in range(1, math.floor(text_length / 2)):
        previous_window = None
        pattern_repeat_count = 0
        total_similarity = 0.0
        for offset in range(0, text_length, scan_window_size):
            window = prepared_text[offset:offset + scan_window_size]
            if previous_window:
                similarity = cosine_similarity(window, previous_window)
                if similarity > similar_threshold:
                    pattern_repeat_count += 1
                    total_similarity += similarity
                else:
                    # This window isn't similar enough to the previous one
                    # Bail out early and try a larger window (next outer loop)
                    break
            previous_window = window
        if pattern_repeat_count == 0:
            continue
        # calculate the penalty
        # if the sum of the lengths of the repeated sequences is less than `min_length_for_full_confidence`
        # then a penatly is applied
        too_short_penalty = min(float((pattern_repeat_count + 1) * scan_window_size) / min_length_for_full_confidence, 1.0)
        prob = (total_similarity / pattern_repeat_count) * too_short_penalty
        if prob > spam_probability:
            spam_probability = prob
    # clamp result to be between 0 and 1
    return min(max(spam_probability, 0), 1)