"""Predict customer intent from message text and browsing behavior."""

import re
from collections.abc import Mapping


class IntentPredictor:
    """Combine regex-based text intent with higher-confidence behavior intent."""

    BUYING = "BUYING"
    CANCELLATION = "CANCELLATION"
    ORDER_TRACKING = "ORDER_TRACKING"
    RETURNING = "RETURNING"
    COMPLAINT = "COMPLAINT"
    BROWSING = "BROWSING"
    READY_TO_BUY = "READY_TO_BUY"
    INTERESTED = "INTERESTED"

    # Word boundaries prevent partial matches such as "help" inside "helper".
    TEXT_PATTERNS = {
        CANCELLATION: re.compile(
            r"\b(?:cancel|end|stop)\b.{0,30}\b(?:subscription|membership|account)\b",
            re.I,
        ),
        BUYING: re.compile(r"\b(?:buy|purchase|price)\b|\badd\s+to\s+cart\b", re.I),
        ORDER_TRACKING: re.compile(r"\b(?:where|order|delivery|arrive)\b", re.I),
        RETURNING: re.compile(r"\b(?:return|refund|cancel|wrong)\b", re.I),
        COMPLAINT: re.compile(r"\b(?:help|problem|issue|annoyed)\b", re.I),
    }

    def predict_intent(
        self,
        text: str,
        behavior_data: Mapping[str, int | float] | None = None,
    ) -> str:
        """Return the combined customer intent.

        Behavior wins when it provides a meaningful signal because actions such as
        clicking the buy button are generally stronger evidence than message words.
        If behavior is inconclusive, the text intent is returned.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        text_intent = self._predict_text_intent(text)
        behavior_intent = self._predict_behavior_intent(behavior_data)

        # Explicit support/cancellation language is stronger than passive browsing
        # metrics. This prevents a customer threatening to cancel from being treated
        # as a buyer merely because demo behavior values are high.
        text_priority_intents = {
            self.CANCELLATION,
            self.RETURNING,
            self.COMPLAINT,
        }
        if text_intent in text_priority_intents:
            return text_intent

        return behavior_intent if behavior_intent is not None else text_intent

    def _predict_text_intent(self, text: str) -> str:
        """Return the first matching text intent, or BROWSING by default."""
        for intent, pattern in self.TEXT_PATTERNS.items():
            if pattern.search(text):
                return intent
        return self.BROWSING

    def _predict_behavior_intent(
        self, behavior_data: Mapping[str, int | float] | None
    ) -> str | None:
        """Return a behavior intent or None when behavior is inconclusive."""
        if behavior_data is None:
            return None
        if not isinstance(behavior_data, Mapping):
            raise TypeError("behavior_data must be a mapping or None")

        scroll_count = self._read_non_negative_number(
            behavior_data, "scroll_count"
        )
        hover_time = self._read_non_negative_number(behavior_data, "hover_time")
        clicks_on_buy = self._read_non_negative_number(
            behavior_data, "clicks_on_buy"
        )

        # A buy-button click is the strongest possible behavioral purchase signal.
        if clicks_on_buy > 0:
            return self.BUYING
        if scroll_count > 2 and hover_time > 5:
            return self.READY_TO_BUY
        if scroll_count > 1 and hover_time > 3:
            return self.INTERESTED
        return None

    @staticmethod
    def _read_non_negative_number(
        behavior_data: Mapping[str, int | float], key: str
    ) -> float:
        """Read and validate a behavior metric, defaulting missing values to zero."""
        value = behavior_data.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"behavior_data[{key!r}] must be a number")
        if value < 0:
            raise ValueError(f"behavior_data[{key!r}] cannot be negative")
        return float(value)


if __name__ == "__main__":
    predictor = IntentPredictor()

    examples = [
        # Text alone identifies a purchase question.
        ("What is the price?", None, "BUYING"),
        # Strong browsing behavior overrides the order-related text match.
        (
            "Where can I find this order option?",
            {"scroll_count": 3, "hover_time": 6, "clicks_on_buy": 0},
            "READY_TO_BUY",
        ),
        # Clicking Buy is stronger evidence than complaint language.
        (
            "I have a problem with the product details.",
            {"scroll_count": 1, "hover_time": 2, "clicks_on_buy": 2},
            "BUYING",
        ),
    ]

    for message, behavior, expected in examples:
        result = predictor.predict_intent(message, behavior)
        print(
            f"Text: {message!r}\n"
            f"Behavior: {behavior}\n"
            f"Intent: {result} (expected {expected})\n"
        )
        assert result == expected
