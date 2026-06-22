"""Streamlit interface for the AI Emotion & Intent Predictor Bot."""

import os
from typing import Any

import streamlit as st

from auto_actions import AutoActionBot

# ── API key & model ──────────────────────────────────────────────────────────
# Set your key here directly, or keep it in the OPENAI_API_KEY environment var.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Emotion & Intent Predictor",
    page_icon="🤖",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    .hero-title {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .hero-sub {
        text-align: center;
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    .chat-bubble-user {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        padding: 0.9rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(99,102,241,0.4);
        font-size: 0.97rem;
    }

    .chat-bubble-bot {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        backdrop-filter: blur(12px);
        color: #e2e8f0;
        padding: 0.9rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        max-width: 85%;
        font-size: 0.97rem;
    }

    .tag-pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 99px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px 4px 2px 0;
    }

    .tag-emotion { background: rgba(167,139,250,0.2); color: #c4b5fd; border: 1px solid #7c3aed; }
    .tag-intent  { background: rgba(96,165,250,0.2);  color: #93c5fd; border: 1px solid #3b82f6; }

    .action-box {
        background: rgba(251,191,36,0.08);
        border: 1px solid rgba(251,191,36,0.35);
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-top: 0.6rem;
        color: #fde68a;
        font-size: 0.87rem;
    }

    .demo-btn {
        margin-top: 1rem;
    }

    div[data-testid="stTextArea"] textarea {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124,58,237,0.3) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(124,58,237,0.45) !important;
    }

    hr { border-color: rgba(255,255,255,0.08) !important; }

    .footer-note {
        text-align: center;
        color: #475569;
        font-size: 0.78rem;
        margin-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Emoji maps ────────────────────────────────────────────────────────────────
EMOTION_EMOJIS = {
    "HAPPY": "😊",
    "NEUTRAL": "😐",
    "FRUSTRATED": "😣",
    "ANGRY": "😡",
}

INTENT_EMOJIS = {
    "BUYING": "🛒",
    "CANCELLATION": "🛑",
    "READY_TO_BUY": "💳",
    "INTERESTED": "👀",
    "ORDER_TRACKING": "🚚",
    "RETURNING": "↩️",
    "COMPLAINT": "📣",
    "BROWSING": "🔎",
}

# ── Bot init ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_bot(api_key: str, model: str) -> AutoActionBot:
    """Initialize and cache the bot once."""
    return AutoActionBot(api_key=api_key, model=model)


# ── Chat history ──────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []  # list of {"role": "user"|"bot", "data": ...}


# ── Helpers ───────────────────────────────────────────────────────────────────
def render_bot_bubble(result: dict[str, Any]) -> None:
    emotion = result["emotion"]
    intent = result["intent"]
    action = result["action"]

    emotion_emoji = EMOTION_EMOJIS.get(emotion, "💬")
    intent_emoji = INTENT_EMOJIS.get(intent, "🎯")

    tags = (
        f'<span class="tag-pill tag-emotion">{emotion_emoji} {emotion}</span>'
        f'<span class="tag-pill tag-intent">{intent_emoji} {intent.replace("_", " ")}</span>'
    )

    response_html = result["response"].replace("\n", "<br>")

    action_html = ""
    if action["type"] != "NONE":
        parts = [f"<b>⚡ {action['type']}</b>"]
        if action.get("amount") is not None:
            parts.append(f"Amount: ₹{action['amount']}")
        if action.get("code") is not None:
            parts.append(f"Code: <code>SAVE{action['code']}</code>")
        parts.append(f"Reason: {action['reason']}")
        action_html = f'<div class="action-box">{"&nbsp;&nbsp;|&nbsp;&nbsp;".join(parts)}</div>'

    st.markdown(
        f"""
        <div class="chat-bubble-bot">
            <div style="margin-bottom:0.5rem;">{tags}</div>
            <div>{response_html}</div>
            {action_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def analyze_and_respond(message: str, behavior: dict) -> None:
    """Run bot, store result in history, and render."""
    # User bubble
    st.session_state.history.append({"role": "user", "text": message})
    try:
        # Determine the key/model to use (env -> default)
        model = os.getenv("OPENAI_MODEL") or OPENAI_MODEL
        api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        
        result = get_bot(api_key, model).handle_customer(message, behavior)
        st.session_state.history.append({"role": "bot", "data": result})
    except EnvironmentError:
        st.session_state.history.append({
            "role": "bot",
            "data": None,
            "error": "⚠️ OpenAI API key is missing or invalid. Set OPENAI_API_KEY.",
        })
    except RuntimeError as e:
        st.session_state.history.append({"role": "bot", "data": None, "error": str(e)})
    except Exception as e:
        st.session_state.history.append({"role": "bot", "data": None, "error": f"Error: {e}"})


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">🤖 AI Emotion & Intent Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Customer support bot that reads emotion and intent — then responds instantly</div>', unsafe_allow_html=True)

# Render chat history
for entry in st.session_state.history:
    if entry["role"] == "user":
        st.markdown(
            f'<div class="chat-bubble-user">{entry["text"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        if entry.get("error"):
            st.error(entry["error"])
        elif entry.get("data"):
            render_bot_bubble(entry["data"])

st.markdown("---")

# Input area
with st.form(key="chat_form", clear_on_submit=True):
    customer_message = st.text_area(
        "💬 Your message",
        placeholder="e.g. I'm really frustrated, my order still hasn't arrived...",
        height=110,
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        submitted = st.form_submit_button("➤ Send", use_container_width=True)
    with col2:
        scroll_count = st.number_input("Scrolls", min_value=0, value=0, step=1)
    with col3:
        hover_time = st.number_input("Hover (s)", min_value=0.0, value=0.0, step=1.0)

if submitted and customer_message.strip():
    behavior = {
        "scroll_count": scroll_count,
        "hover_time": hover_time,
        "clicks_on_buy": 0,
    }
    analyze_and_respond(customer_message.strip(), behavior)
    st.rerun()

st.markdown("---")

# Demo button
if st.button("🎬 Try Demo Examples", use_container_width=True):
    demos = [
        {
            "message": "THIS IS UNACCEPTABLE!! I am angry about this problem.",
            "behavior": {"scroll_count": 0, "hover_time": 0, "clicks_on_buy": 0},
        },
        {
            "message": "I want to buy this product, but I am still deciding.",
            "behavior": {"scroll_count": 3, "hover_time": 6, "clicks_on_buy": 0},
        },
        {
            "message": "I received the wrong item and want to return it.",
            "behavior": {"scroll_count": 0, "hover_time": 0, "clicks_on_buy": 0, "refund_amount": 100},
        },
    ]
    for demo in demos:
        analyze_and_respond(demo["message"], demo["behavior"])
    st.rerun()

if st.session_state.history and st.button("🗑️ Clear Chat", use_container_width=False):
    st.session_state.history = []
    st.rerun()

st.markdown(
    '<div class="footer-note">Demo actions require validation and integration with real support, order, and payment systems before production use.</div>',
    unsafe_allow_html=True,
)
