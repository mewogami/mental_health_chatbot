import streamlit as st
from groq import Groq
import config
import re

st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠")
st.title("🧠 Mental Health Chatbot")

# ---- Session State Initialization ----
if "messages" not in st.session_state:
    st.session_state.messages = []
if "scroll_to_bottom" not in st.session_state:
    st.session_state.scroll_to_bottom = False

# ---- Groq Client Initialization ----
client = Groq(api_key=config.API_KEY)

# ---- Sidebar for Prompt Tweaking ----
st.sidebar.header("Chatbot Settings")
default_prompt = (
    "You are a compassionate mental health assistant. "
    "Only answer mental health-related questions. For other topics, respond: "
    "'I specialize in mental health. How can I support you today?'"
)
system_prompt = st.sidebar.text_area(
    "System Prompt:",
    value=default_prompt,
    height=150,
    key="unique_system_prompt"
)
model_name = config.AI_MODEL

# ---- Helper: Parse <think> Section ----
def parse_thinking_and_output(text):
    thinking = None
    final_output = text
    match = re.search(r'<think>(.*?)<\/think>', text, re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        final_output = re.sub(r'<think>.*?<\/think>', '', text, flags=re.DOTALL).strip()
    return thinking, final_output

# ---- Display Chat History ----
st.markdown('<div id="chat-history">', unsafe_allow_html=True)
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
            if "thinking" in msg and msg["thinking"]:
                with st.expander("Show how I thought"):
                    st.markdown(msg["thinking"])
st.markdown('</div>', unsafe_allow_html=True)

# ---- Anchor for Auto-Scroll ----
st.markdown('<div id="end-of-chat"></div>', unsafe_allow_html=True)

# ---- Chat Input and Response ----
user_input = st.chat_input("How can I support your mental health today?")

if user_input:
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.scroll_to_bottom = True  # Set flag to scroll after response

    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare messages for Groq (system + history)
    groq_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m["role"] != "system"
    ] + [{"role": "system", "content": system_prompt}]

    # Create assistant message placeholder
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            # Streaming response from Groq
            stream = client.chat.completions.create(
                model=model_name,
                messages=groq_messages,
                temperature=0.6,
                max_tokens=4096,
                top_p=0.95,
                stream=True
            )
            # Collect full response silently
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content

            # Parse <think> and final output
            thinking, final_output = parse_thinking_and_output(full_response)

            # Display only the final output
            response_placeholder.markdown(final_output)
            if thinking:
                with st.expander("Show how I thought"):
                    st.markdown(thinking)

            # Store both final output and thinking in chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_output,
                "thinking": thinking
            })

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

# ---- Inject JavaScript to scroll to bottom ONLY if needed ----
if st.session_state.scroll_to_bottom:
    st.markdown("""
    <script>
    function scrollToBottom() {
        var element = document.getElementById("end-of-chat");
        if (element) {
            element.scrollIntoView({behavior: "smooth"});
        }
    }
    setTimeout(scrollToBottom, 200);
    setTimeout(scrollToBottom, 600);
    setTimeout(scrollToBottom, 1200);
    </script>
    """, unsafe_allow_html=True)
    st.session_state.scroll_to_bottom = False  # Reset flag
