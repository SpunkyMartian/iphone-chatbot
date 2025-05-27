import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="iPhone Expert Assistant",
    page_icon="📱",
    layout="centered"
)

# Custom CSS
st.markdown("""
    <style>
    .stTextInput>div>div>input {
        background-color: #f0f2f6;
        color: #000000;
    }
    .stButton>button {
        width: 100%;
        background-color: #007AFF;
        color: white;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #007AFF;
        color: white;
    }
    .chat-message.assistant {
        background-color: #e0e0e0;
        color: #222222;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# App title and description
st.title("📱 iPhone Expert Assistant")
st.markdown("""
    Your personal iPhone expert! Ask me anything about:
    - iPhone models and specifications
    - iOS features and updates
    - Troubleshooting
    - Settings and customization
    - Camera features
    - App Store and apps
    - iCloud and backup
    - Accessories
    - And more!
""")

# System prompt
SYSTEM_PROMPT = """
You are an expert iPhone assistant with comprehensive, up-to-date knowledge about all iPhone models, iOS, and the Apple ecosystem.

Your job is to answer user questions about iPhones, iOS, and related Apple products and services. Please follow these rules strictly:

- Only answer the user's specific question. Do not provide extra context, background, or related information unless the user explicitly asks for it.
- Do not speculate or make assumptions. If you do not know the answer, or if the information is not available, say so clearly and suggest checking the official Apple website or documentation.
- Never mention unrelated products, brands, or accessories unless the user asks about them directly.
- If the user's question is ambiguous, politely ask for clarification before answering.
- Keep your answers concise, factual, and directly relevant to the user's question.
- Do not repeat information from previous answers unless the user asks for a summary or follow-up.
- If the user uses ambiguous references (like "it" or "that one"), assume they mean the last topic discussed, unless the context clearly indicates otherwise.
- Do not use trending topics or news in your answers but rather stick to the topic of the conversation.
- Do not mention features, controversies, comparisons, or reasons for missing features unless the user specifically asks about them.
- **You must only answer questions about iPhones, iOS, or the Apple ecosystem. If the user asks about any other topic, product, brand, or company (such as Tesla, Samsung, Android, etc.), politely refuse and state: "I'm sorry, I can only answer questions about iPhones, iOS, and the Apple ecosystem."**

You have access to the full recent conversation history (as much as fits in the context window). Always use this context to answer follow-up questions and resolve references to previous answers or questions. If the conversation is long, prioritize the most recent exchanges for context.

If you cannot answer a question, simply state: "I'm sorry, I don't have that information. Please check the official Apple website or contact Apple support."
"""

def get_ai_response(user_message):
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        return "Error: Perplexity API key not configured. Please set the PERPLEXITY_API_KEY environment variable."
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Build the full message history for context (limit to last 100 exchanges, filter out empty content)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    filtered_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
        if msg["role"] in ["user", "assistant"] and msg["content"].strip() != ""
    ]
    filtered_history = filtered_history[-100:]
    messages.extend(filtered_history)
    # Add the new user message (not yet in session state)
    if user_message.strip() != "":
        messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama-3.1-sonar-large-128k-online",
        "messages": messages,
        "max_tokens": 5000,
        "temperature": 0.2,
        "top_p": 0.9,
        "return_citations": True,
        "search_domain_filter": ["apple.com"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        elif response.status_code == 400:
            st.error("API request failed with status code 400. See payload below:")
            st.json(payload)
            return f"Error: API request failed with status code 400"
        else:
            return f"Error: API request failed with status code {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

# Display chat messages
for message in st.session_state.messages:
    with st.container():
        st.markdown(f"""
            <div class="chat-message {message['role']}">
                <div>{message['content']}</div>
            </div>
        """, unsafe_allow_html=True)

# Chat input using a form to prevent infinite loop and allow clearing
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask me anything about your iPhone:", key="user_input")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    # Get AI response (do NOT add user message to session state yet)
    with st.spinner("Thinking..."):
        ai_response = get_ai_response(user_input)
    # Only add user and assistant messages if not an error
    if not ai_response.startswith("Error: API request failed with status code 400"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
    # If there is a 400 error, do not rerun so the error and payload remain visible 