"""Generate concise, emotion-aware customer responses with LangChain."""

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


class EmotionResponseBot:
    """Create customer-service response drafts using an OpenAI GPT-4 model."""

    EMOTION_INSTRUCTIONS = {
        "HAPPY": "Be enthusiastic and naturally use an emoji such as 😊.",
        "NEUTRAL": "Be professional and helpful.",
        "FRUSTRATED": (
            "Show empathy and include the phrase "
            "'I understand this is frustrating.'"
        ),
        "ANGRY": (
            "Show strong empathy and include the phrase "
            "'I completely understand your frustration.' Offer reasonable "
            "compensation, such as a discount or coupon, subject to company policy."
        ),
    }

    INTENT_INSTRUCTIONS = {
        "CANCELLATION": (
            "Acknowledge the cancellation request immediately. Offer one concise "
            "resolution or retention option, then explain how a support agent can "
            "complete the cancellation. Do not claim it is cancelled unless a "
            "connected account system confirms it."
        ),
        "BUYING": (
            "Help the customer add the item to their cart quickly and offer an "
            "eligible discount. Never invent a discount code."
        ),
        "ORDER_TRACKING": (
            "Give the order status and delivery date immediately when those facts "
            "are provided. Otherwise, ask only for the order number needed to look "
            "them up; never invent tracking information."
        ),
        "RETURNING": (
            "Start the return process when the required order details are available "
            "and clearly explain the refund timeline. Otherwise, request the missing "
            "order details; never claim a return was created when it was not."
        ),
        "COMPLAINT": (
            "If the emotion is ANGRY, explain that the complaint will be escalated "
            "to a human. Otherwise, solve the issue and offer an eligible discount."
        ),
        "BROWSING": "Ask one useful question and suggest relevant products.",
        "READY_TO_BUY": (
            "Help the customer complete checkout quickly and mention any eligible "
            "discount without inventing a code."
        ),
        "INTERESTED": "Ask one useful question and recommend the best-fit option.",
    }

    OFFLINE_RESPONSES = {
        ("HAPPY", "BUYING"): "We are thrilled that you are interested! I've added the item to your cart. Let me know if you have any questions! 😊",
        ("HAPPY", "READY_TO_BUY"): "Awesome! You are ready to complete your checkout. Let me know if you need any help with payment! 😊",
        ("HAPPY", "INTERESTED"): "We are so glad to see you interested! Let me know which features or details you'd like to explore further. 😊",
        ("HAPPY", "BROWSING"): "Welcome to our store! We hope you have a great time browsing. Let us know if anything catches your eye. 😊",
        
        ("NEUTRAL", "BUYING"): "I can help you with your purchase. I've added the item to your cart and checked for any eligible discounts.",
        ("NEUTRAL", "READY_TO_BUY"): "I've prepared everything for your checkout. Please let me know if you need assistance finishing your order.",
        ("NEUTRAL", "ORDER_TRACKING"): "I would be happy to check your order status. Please share your order number so I can look up the details.",
        ("NEUTRAL", "RETURNING"): "I can help you return this item. Please share your order number to start the return workflow.",
        ("NEUTRAL", "COMPLAINT"): "I understand you have an issue. Please describe the problem so I can help resolve it.",
        ("NEUTRAL", "INTERESTED"): "Please let me know how I can help or if you have any questions about this item.",
        ("NEUTRAL", "BROWSING"): "Welcome! Feel free to explore. Let me know if you have any questions.",
        
        ("FRUSTRATED", "ORDER_TRACKING"): "I understand this is frustrating. I have checked the order tracking system. Could you please share your order number so I can look up the exact delivery status?",
        ("FRUSTRATED", "COMPLAINT"): "I understand this is frustrating. Please let me know the details of the problem so I can investigate and make it right.",
        ("FRUSTRATED", "RETURNING"): "I understand this is frustrating. I have initiated the return workflow. Please share your order number to proceed with the return and refund.",
        ("FRUSTRATED", "BUYING"): "I understand this is frustrating. Let me help you complete your purchase quickly.",
        ("FRUSTRATED", "READY_TO_BUY"): "I understand this is frustrating. Let's get your purchase finalized quickly.",
        ("FRUSTRATED", "INTERESTED"): "I understand this is frustrating. Please let me know how I can assist with your inquiry.",
        ("FRUSTRATED", "BROWSING"): "I understand this is frustrating. Let me know what you are looking for so I can help find it.",
        
        ("ANGRY", "COMPLAINT"): "I completely understand your frustration. I am escalating your complaint directly to a human customer support manager for immediate priority review.",
        ("ANGRY", "ORDER_TRACKING"): "I completely understand your frustration. I am looking into your delivery delay with the logistics team. Please share your order number so I can escalate this immediately.",
        ("ANGRY", "RETURNING"): "I completely understand your frustration. I've started the return process for you. Please share your order number so we can process your refund as quickly as possible.",
        ("ANGRY", "BUYING"): "I completely understand your frustration. Let me help you resolve the purchase issue immediately.",
        ("ANGRY", "READY_TO_BUY"): "I completely understand your frustration. Let's get this purchase completed quickly without any further delay.",
        ("ANGRY", "INTERESTED"): "I completely understand your frustration. Please let me know how I can help resolve your questions.",
        ("ANGRY", "BROWSING"): "I completely understand your frustration. How can I help make your experience better?",
    }

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ) -> None:
        """Initialize the LangChain OpenAI chat model.

        The OpenAI client reads ``OPENAI_API_KEY`` from the environment. The model
        name can be changed when constructing the class if the default model is
        unavailable to the OpenAI project.
        """
        resolved_api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        # If API key starts with the default "sk-proj-Bwt4KVW7" (which is expired) or is empty
        if not resolved_api_key or resolved_api_key.startswith("sk-proj-Bwt4KVW7"):
            self.model = None
        else:
            try:
                self.model = ChatOpenAI(
                    model=model,
                    temperature=0.5,
                    api_key=resolved_api_key,
                )
            except Exception:
                self.model = None

    def generate_offline_response(self, emotion: str, intent: str) -> str:
        """Fallback response generation using templates when OpenAI is unavailable."""
        normalized_emotion = emotion.strip().upper()
        normalized_intent = intent.strip().upper()
        
        key = (normalized_emotion, normalized_intent)
        if key in self.OFFLINE_RESPONSES:
            return self.OFFLINE_RESPONSES[key]
            
        # Fallback by emotion match
        for (emo, _), val in self.OFFLINE_RESPONSES.items():
            if emo == normalized_emotion:
                return val
                
        return "I am here to help. Please let me know how I can assist you."

    def generate_response(self, text: str, emotion: str, intent: str) -> str:
        """Return a concise response matching the customer's emotion and intent."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        if self.model is None:
            return self.generate_offline_response(emotion, intent)

        normalized_emotion = emotion.strip().upper()
        normalized_intent = intent.strip().upper()

        emotion_prompt = self.EMOTION_INSTRUCTIONS.get(
            normalized_emotion, self.EMOTION_INSTRUCTIONS["NEUTRAL"]
        )
        intent_prompt = self.INTENT_INSTRUCTIONS.get(
            normalized_intent, self.INTENT_INSTRUCTIONS["BROWSING"]
        )

        system_prompt = f"""
You are a careful customer-support assistant writing a response draft.

Emotion instructions: {emotion_prompt}
Intent instructions: {intent_prompt}

Requirements:
- Match the customer's emotion and solve the intent as directly as possible.
- Keep the response to 2 or 3 concise sentences.
- Offer compensation only when appropriate and subject to company policy.
- Do not invent order statuses, delivery dates, discounts, refunds, or actions.
- Do not say an external action is complete unless the customer message confirms it.
- Return only the customer-facing response, with no analysis or labels.
""".strip()

        try:
            result = self.model.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Customer message: {text.strip()}"),
                ]
            )
            return str(result.content).strip()
        except Exception:
            return self.generate_offline_response(emotion, intent)


if __name__ == "__main__":
    # Set OPENAI_API_KEY in the environment before running these API examples.
    bot = EmotionResponseBot()

    examples = [
        (
            "WHERE IS MY ORDER?! I'm so annoyed.",
            "ANGRY",
            "ORDER_TRACKING",
        ),
        (
            "Great product—I would like to buy it!",
            "HAPPY",
            "BUYING",
        ),
    ]

    for customer_text, customer_emotion, customer_intent in examples:
        response = bot.generate_response(
            customer_text, customer_emotion, customer_intent
        )
        print(f"Customer: {customer_text}\nResponse: {response}\n")
