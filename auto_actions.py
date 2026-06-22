"""Orchestrate emotion, intent, response generation, and automatic actions."""

import os
import random
from collections.abc import Mapping
from typing import Any

from emotion_detector import EmotionDetector
from intent_predictor import IntentPredictor
from response_generator import EmotionResponseBot


class AutoActionBot:
    """Analyze a customer and return a response plus a recommended action."""

    def __init__(
        self,
        response_bot: Any | None = None,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Initialize the three specialized components.

        ``response_bot`` supports dependency injection for offline tests. Normal
        application code should omit it to use ``EmotionResponseBot``.
        """
        self.emotion_detector = EmotionDetector()
        self.intent_predictor = IntentPredictor()
        self.response_bot = (
            response_bot
            if response_bot is not None
            else EmotionResponseBot(api_key=api_key, model=model)
        )

    def handle_customer(
        self,
        text: str,
        behavior_data: Mapping[str, int | float] | None = None,
    ) -> dict[str, Any]:
        """Analyze a message and return emotion, intent, response, and action.

        ``AUTO_RETURN`` is an instruction for a connected commerce workflow. This
        demonstration does not directly modify an order or issue money by itself.
        """
        behavior = self._normalize_behavior(behavior_data)

        # Step 1: Detect emotion and intent. Typing speed is an optional behavior
        # metric understood by EmotionDetector.
        typing_speed = behavior.get("typing_speed")
        emotion, sentiment_score = self.emotion_detector.detect_emotion(
            text, typing_speed=typing_speed
        )
        intent = self.intent_predictor.predict_intent(text, behavior)

        # Step 2: Select the highest-priority automatic action.
        action = self._choose_action(emotion, intent, behavior)

        # Step 3: Ask the response model for a concise customer-facing draft.
        response = self.response_bot.generate_response(text, emotion, intent)

        # Step 4: Append the concrete action so it cannot be overlooked.
        response = self._append_action(response, action)

        return {
            "emotion": emotion,
            "intent": intent,
            "response": response,
            "action": action,
            "sentiment_score": sentiment_score,
        }

    def _choose_action(
        self,
        emotion: str,
        intent: str,
        behavior: Mapping[str, float],
    ) -> dict[str, Any]:
        """Apply business rules in priority order and return one action."""
        scroll_count = behavior.get("scroll_count", 0)
        hover_time = behavior.get("hover_time", 0)

        if emotion == "ANGRY" and intent == "COMPLAINT":
            return {
                "type": "ESCALATE",
                "amount": None,
                "code": None,
                "reason": "Angry complaints require immediate human review.",
            }

        if intent == "CANCELLATION":
            return {
                "type": "ESCALATE",
                "amount": None,
                "code": None,
                "reason": (
                    "Route the cancellation risk to a human retention/support "
                    "agent without issuing an unrelated purchase discount."
                ),
            }

        if emotion == "FRUSTRATED" and intent == "ORDER_TRACKING":
            return self._discount_action(
                amount=100,
                reason="Compensation for a frustrating order-tracking experience.",
            )

        # IntentPredictor labels strong browsing behavior as READY_TO_BUY. Treat it
        # as part of the buying family so the hesitant-buyer rule remains reachable.
        if (
            intent in {"BUYING", "READY_TO_BUY"}
            and hover_time > 5
            and scroll_count > 2
        ):
            return self._discount_action(
                amount=200,
                reason="Purchase incentive for a highly engaged, hesitant buyer.",
            )

        if intent == "RETURNING":
            refund_amount = behavior.get("refund_amount", 100)
            return {
                "type": "AUTO_RETURN",
                "amount": self._clean_amount(refund_amount, "refund_amount"),
                "code": None,
                "reason": "Start the return workflow and prepare the refund.",
            }

        return {
            "type": "NONE",
            "amount": None,
            "code": None,
            "reason": "No automatic action is required.",
        }

    @staticmethod
    def _discount_action(amount: int, reason: str) -> dict[str, Any]:
        """Build a discount action with a four-digit demonstration code."""
        return {
            "type": "DISCOUNT",
            "amount": amount,
            "code": random.randint(1000, 9999),
            "reason": reason,
        }

    @staticmethod
    def _append_action(response: str, action: Mapping[str, Any]) -> str:
        """Add a short, customer-visible action note to the generated response."""
        action_type = action["type"]

        if action_type == "DISCOUNT":
            note = (
                f"Courtesy discount: ₹{action['amount']} with code "
                f"SAVE{action['code']}."
            )
        elif action_type == "ESCALATE":
            note = "Escalation note: a human support agent should review this now."
        elif action_type == "AUTO_RETURN":
            note = (
                f"Return workflow initiated for a proposed refund of "
                f"₹{action['amount']}; final processing requires order validation."
            )
        else:
            return response.strip()

        return f"{response.strip()}\n\n{note}"

    @staticmethod
    def _normalize_behavior(
        behavior_data: Mapping[str, int | float] | None,
    ) -> dict[str, float]:
        """Copy and validate supported behavior values."""
        if behavior_data is None:
            return {}
        if not isinstance(behavior_data, Mapping):
            raise TypeError("behavior_data must be a mapping or None")

        behavior: dict[str, float] = {}
        for key, value in behavior_data.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"behavior_data[{key!r}] must be a number")
            if value < 0:
                raise ValueError(f"behavior_data[{key!r}] cannot be negative")
            behavior[key] = float(value)
        return behavior

    @staticmethod
    def _clean_amount(value: float, field_name: str) -> int | float:
        """Return a clean numeric currency amount after validation."""
        if value < 0:
            raise ValueError(f"{field_name} cannot be negative")
        return int(value) if float(value).is_integer() else round(float(value), 2)


if __name__ == "__main__":
    class OfflineResponseBot:
        """Small test double used only when an OpenAI key is unavailable."""

        @staticmethod
        def generate_response(text: str, emotion: str, intent: str) -> str:
            return f"Offline test response for {emotion}/{intent}."


    if os.getenv("OPENAI_API_KEY"):
        bot = AutoActionBot()
        print("Running examples with OpenAI responses.")
    else:
        bot = AutoActionBot(response_bot=OfflineResponseBot())
        print(
            "OPENAI_API_KEY is not set; testing detection and actions with "
            "offline response text."
        )

    examples = [
        {
            "name": "Angry complaint",
            "text": "THIS IS UNACCEPTABLE!! I have a terrible problem.",
            "behavior": None,
            "expected_action": "ESCALATE",
        },
        {
            "name": "Frustrated order tracking",
            "text": "My delivery is late and this is frustrating.",
            "behavior": None,
            "expected_action": "DISCOUNT",
        },
        {
            "name": "Hesitant buyer",
            "text": "I want to buy this, but I am still deciding.",
            "behavior": {
                "scroll_count": 3,
                "hover_time": 6,
                "clicks_on_buy": 0,
            },
            "expected_action": "DISCOUNT",
        },
        {
            "name": "Return request",
            "text": "I received the wrong item and want to return it.",
            "behavior": {"refund_amount": 1499},
            "expected_action": "AUTO_RETURN",
        },
    ]

    for example in examples:
        result = bot.handle_customer(example["text"], example["behavior"])
        print(f"\n--- {example['name']} ---")
        print(result)
        assert result["action"]["type"] == example["expected_action"]
