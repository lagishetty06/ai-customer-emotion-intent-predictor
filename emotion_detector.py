
"""Customer emotion detection using TextBlob only."""

import re
from textblob import TextBlob


class EmotionDetector:
    HAPPY = "HAPPY"
    NEUTRAL = "NEUTRAL"
    FRUSTRATED = "FRUSTRATED"
    ANGRY = "ANGRY"

    ANGER_WORDS = {
        "angry",
        "annoyed",
        "furious",
        "hate",
        "outraged",
        "ridiculous",
        "terrible",
        "unacceptable",
        "worst",
    }

    def __init__(self):
        pass

    def detect_emotion(self, text: str, typing_speed=None):
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        cleaned_text = text.strip()

        if not cleaned_text:
            return self.NEUTRAL, 0.0

        sentiment_score = float(
            TextBlob(cleaned_text).sentiment.polarity
        )

        sentiment_score = round(
            max(-1.0, min(1.0, sentiment_score)),
            3,
        )

        words = re.findall(r"[A-Za-z']+", cleaned_text)

        lowercase_words = {word.lower() for word in words}

        angry_word_found = bool(
            lowercase_words & self.ANGER_WORDS
        )

        uppercase_words = [
            word for word in words
            if len(word) > 1 and word.isupper()
        ]

        mostly_uppercase = len(uppercase_words) >= 2

        aggressive_punctuation = bool(
            re.search(r"[!?]{2,}", cleaned_text)
        )

        anger_signals = sum(
            (
                angry_word_found,
                mostly_uppercase,
                aggressive_punctuation,
            )
        )

        if sentiment_score <= -0.65 or anger_signals >= 2:
            emotion = self.ANGRY
        elif sentiment_score <= -0.2 or angry_word_found:
            emotion = self.FRUSTRATED
        elif sentiment_score >= 0.2:
            emotion = self.HAPPY
        else:
            emotion = self.NEUTRAL

        return emotion, sentiment_score

