from http.server import BaseHTTPRequestHandler
import json
import os
import requests

def handler(request):
    try:
        # Read request body
        content_length = int(request.headers.get('Content-Length', 0))
        post_data = request.body
        data = json.loads(post_data.decode('utf-8'))
        
        user_message = data.get('message', '')
        
        if not user_message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No message provided'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            }
        
        # iPhone expert system prompt
        system_prompt = """You are an expert iPhone assistant with comprehensive knowledge about all iPhone models, iOS, and the Apple ecosystem.

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

For every follow-up question, use the last iPhone model or topic discussed in the conversation as the default subject, unless the user specifies otherwise. If the user asks about 'it', 'that one', or uses another ambiguous reference, assume they mean the last iPhone model or topic mentioned. If you are unsure, politely ask the user to clarify.

You have access to the full recent conversation history (as much as fits in the context window). Always use this context to answer follow-up questions and resolve references to previous answers or questions. If the conversation is long, prioritize the most recent exchanges for context.

Answer questions only related to iPhone and Apple ecosystem and don't engage in anything else.
"""

        # Get Perplexity API key
        api_key = os.environ.get('PERPLEXITY_API_KEY')
        
        if not api_key:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Perplexity API key not configured'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # Perplexity API call
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
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
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {
                'statusCode': response.status_code,
                'body': json.dumps({'error': f'API error: {response.status_code}'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        response_data = response.json()
        assistant_response = response_data['choices'][0]['message']['content']
        
        # Get citations if available
        citations = []
        if 'citations' in response_data:
            citations = response_data['citations']
        
        # Return response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': assistant_response,
                'citations': citations,
                'status': 'success'
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
        
    except requests.exceptions.Timeout:
        return {
            'statusCode': 504,
            'body': json.dumps({'error': 'Request timeout. Please try again.'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }