"""Customer emotion detection using TextBlob and NLTK VADER."""

import re

from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob


class EmotionDetector:
    """Classify customer text as HAPPY, NEUTRAL, FRUSTRATED, or ANGRY."""

    HAPPY = "HAPPY"
    NEUTRAL = "NEUTRAL"
    FRUSTRATED = "FRUSTRATED"
    ANGRY = "ANGRY"

    # These terms distinguish anger from ordinary negative sentiment.
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

    def __init__(self) -> None:
        """Initialize VADER.

        Before first use, install its data with:
        ``python -m nltk.downloader vader_lexicon``
        """
        try:
            self.vader = SentimentIntensityAnalyzer()
        except LookupError as error:
            raise RuntimeError(
                "VADER data is missing. Run: "
                "python -m nltk.downloader vader_lexicon"
            ) from error

    def detect_emotion(
        self, text: str, typing_speed: float | None = None
    ) -> tuple[str, float]:
        """Return ``(emotion, sentiment_score)`` for a customer message.

        The sentiment score combines TextBlob polarity and VADER's compound score.
        Both inputs—and therefore the returned score—range from -1.0 to +1.0.
        A typing speed below 10 words per minute is treated as frustration unless
        the message contains stronger signs of anger.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if typing_speed is not None and typing_speed < 0:
            raise ValueError("typing_speed cannot be negative")

        cleaned_text = text.strip()
        if not cleaned_text:
            return self.NEUTRAL, 0.0

        textblob_score = float(TextBlob(cleaned_text).sentiment.polarity)
        vader_score = float(self.vader.polarity_scores(cleaned_text)["compound"])

        # VADER receives slightly more weight because it accounts for capitalization,
        # punctuation, intensifiers, and negation in short social-style messages.
        sentiment_score = (0.4 * textblob_score) + (0.6 * vader_score)
        sentiment_score = round(max(-1.0, min(1.0, sentiment_score)), 3)

        words = re.findall(r"[A-Za-z']+", cleaned_text)
        lowercase_words = {word.lower() for word in words}
        angry_word_found = bool(lowercase_words & self.ANGER_WORDS)
        uppercase_words = [word for word in words if len(word) > 1 and word.isupper()]
        mostly_uppercase = len(uppercase_words) >= 2
        aggressive_punctuation = bool(re.search(r"[!?]{2,}", cleaned_text))

        anger_signals = sum(
            (angry_word_found, mostly_uppercase, aggressive_punctuation)
        )

        # Explicit anger cues take priority over the typing-speed signal.
        if sentiment_score <= -0.65 or anger_signals >= 2:
            emotion = self.ANGRY
        elif typing_speed is not None and typing_speed < 10:
            emotion = self.FRUSTRATED
        elif sentiment_score <= -0.2 or angry_word_found:
            emotion = self.FRUSTRATED
        elif sentiment_score >= 0.2:
            emotion = self.HAPPY
        else:
            emotion = self.NEUTRAL

        return emotion, sentiment_score


if __name__ == "__main__":
    detector = EmotionDetector()

    examples = [
        ("WHERE IS MY ORDER?! I'm so annoyed", "ANGRY"),
        ("Great product, love it!", "HAPPY"),
        ("What's the price?", "NEUTRAL"),
    ]

    for message, expected_emotion in examples:
        detected_emotion, score = detector.detect_emotion(message)
        print(
            f"Text: {message!r}\n"
            f"Emotion: {detected_emotion} (expected {expected_emotion})\n"
            f"Sentiment score: {score:+.3f}\n"
        )
        assert detected_emotion == expected_emotion
