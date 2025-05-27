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
SYSTEM_PROMPT = """You are an expert iPhone assistant with comprehensive knowledge about all iPhone models, iOS, and Apple ecosystem.

You can help with:
- iPhone specifications and comparisons (iPhone 15, 14, 13, 12, 11, XR, XS, X, 8, 7, SE)
- iOS features and updates  
- Troubleshooting (battery, storage, connectivity, performance, apps)
- Settings and customization
- Camera features and photography tips
- App Store and app management
- iCloud and data backup/sync
- Accessories and compatibility
- Repair and maintenance advice
- Security and privacy features
- Tips and tricks for better iPhone usage

Always provide accurate, helpful, and friendly responses. If unsure about something, say so rather than guessing. Keep responses concise but thorough.
Answer questions only related to iPhone and Apple ecosystem and dont engage in anything else. """

def get_ai_response(user_message):
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        return "Error: Perplexity API key not configured. Please set the PERPLEXITY_API_KEY environment variable."
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Build the full message history for context (limit to last 10 exchanges, filter out empty content)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    filtered_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
        if msg["role"] in ["user", "assistant"] and msg["content"].strip() != ""
    ]
    filtered_history = filtered_history[-10:]
    messages.extend(filtered_history)
    if user_message.strip() != "":
        messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": messages,
        "max_tokens": 500,
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

    # Debug: Show the payload in the Streamlit app
    st.write("Payload sent to Perplexity API:", payload)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
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
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Get AI response
    with st.spinner("Thinking..."):
        ai_response = get_ai_response(user_input)
    # Add AI response to chat
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    # Rerun to update chat display
    st.rerun() 