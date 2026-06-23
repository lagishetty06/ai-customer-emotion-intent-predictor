
"""Predict customer intent from message text and browsing behavior."""

import re
from collections.abc import Mapping


class IntentPredictor:
    BUYING = "BUYING"
    CANCELLATION = "CANCELLATION"
    ORDER_TRACKING = "ORDER_TRACKING"
    RETURNING = "RETURNING"
    COMPLAINT = "COMPLAINT"
    BROWSING = "BROWSING"
    READY_TO_BUY = "READY_TO_BUY"
    INTERESTED = "INTERESTED"

    TEXT_PATTERNS = {
        CANCELLATION: re.compile(
            r"\b(?:cancel|end|stop)\b.{0,30}\b(?:subscription|membership|account)\b",
            re.I,
        ),

        READY_TO_BUY: re.compile(
            r"\b(?:payment|pay|checkout|place\s+order|complete\s+order|complete\s+payment|ready\s+to\s+buy|ready\s+to\s+purchase)\b",
            re.I,
        ),

        BUYING: re.compile(
            r"\b(?:buy|purchase|price|pricing|cost)\b|\badd\s+to\s+cart\b",
            re.I,
        ),

        ORDER_TRACKING: re.compile(
            r"\b(?:where\s+is\s+my\s+order|order|delivery|tracking|arrive)\b",
            re.I,
        ),

        RETURNING: re.compile(
            r"\b(?:return|refund|wrong\s+item|damaged)\b",
            re.I,
        ),

        COMPLAINT: re.compile(
            r"\b(?:help|problem|issue|annoyed|frustrated|unacceptable)\b",
            re.I,
        ),
    }

    def predict_intent(
        self,
        text: str,
        behavior_data: Mapping[str, int | float] | None = None,
    ) -> str:

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        text_intent = self._predict_text_intent(text)
        behavior_intent = self._predict_behavior_intent(behavior_data)

        text_priority_intents = {
            self.CANCELLATION,
            self.RETURNING,
            self.COMPLAINT,
            self.READY_TO_BUY,
        }

        if text_intent in text_priority_intents:
            return text_intent

        return behavior_intent if behavior_intent is not None else text_intent

    def _predict_text_intent(self, text: str) -> str:
        for intent, pattern in self.TEXT_PATTERNS.items():
            if pattern.search(text):
                return intent

        return self.BROWSING

    def _predict_behavior_intent(
        self,
        behavior_data: Mapping[str, int | float] | None,
    ) -> str | None:

        if behavior_data is None:
            return None

        scroll_count = float(behavior_data.get("scroll_count", 0))
        hover_time = float(behavior_data.get("hover_time", 0))
        clicks_on_buy = float(behavior_data.get("clicks_on_buy", 0))

        if clicks_on_buy > 0:
            return self.BUYING

        if scroll_count > 2 and hover_time > 5:
            return self.READY_TO_BUY

        if scroll_count > 1 and hover_time > 3:
            return self.INTERESTED

        return None


if __name__ == "__main__":
    predictor = IntentPredictor()

    tests = [
        "Can you explain the difference between Premium and Pro?",
        "I am interested in the Premium plan.",
        "I want to buy this product.",
        "I am ready to complete my payment.",
        "How can I pay?",
        "Take me to checkout.",
        "I received the wrong item and want a refund.",
        "Where is my order?",
        "THIS IS UNACCEPTABLE!! I have a problem.",
        "I want to cancel my subscription.",
    ]

    for text in tests:
        print(f"{text}")
        print("Intent:", predictor.predict_intent(text))
        print("-" * 50)

