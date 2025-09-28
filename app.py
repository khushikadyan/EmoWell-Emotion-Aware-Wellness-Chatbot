from flask import Flask, render_template, request, jsonify
import re
import nltk
import requests
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download NLTK data (only needed once)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

app = Flask(__name__, static_folder='static')

# Initialize preprocessing tools
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Your Colab API URL from ngrok
COLAB_API_URL = "https://d2a3585f6966.ngrok-free.app"

def preprocess_text(text):
    """
    Cleans and preprocesses the input text.
    Steps:
    1. Lowercase the text
    2. Remove punctuation and special characters
    3. Tokenize (split into words)
    4. Remove stopwords (optional, can sometimes remove emotional context)
    5. Lemmatize (get the root word)
    """
    # 1. Lowercase
    text = text.lower()
    # 2. Remove punctuation & special chars (keep letters and spaces)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # 3. Normalize repeated characters
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)  # e.g., sooooo → soo
    # 4. Tokenize
    tokens = nltk.word_tokenize(text)
    # 5. Remove stopwords and lemmatize
    cleaned_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    # Join the tokens back into a single string
    processed_text = ' '.join(cleaned_tokens)
    
    # For debugging, let's print to the console
    print(f"Original text: {text}")
    print(f"Processed text: {processed_text}")
    
    return processed_text

def call_colab_api(text):
    """
    Calls your Colab API to get emotion prediction
    """
    try:
        # Send the text to your Colab API
        response = requests.post(
            f"{COLAB_API_URL}/predict",
            json={"text": text},
            headers={'Content-Type': 'application/json'},
            timeout=10  # Add timeout to prevent hanging
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API error: {response.status_code}, {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to Colab API")
        return None
    except requests.exceptions.Timeout:
        print("Timeout error: Colab API took too long to respond")
        return None
    except Exception as e:
        print(f"Error calling Colab API: {e}")
        return None

def generate_response(emotion, confidence, text):
    """
    Generates a contextual response based on the detected emotion
    """
    responses = {
        'joy': [
            "It's wonderful to hear you're feeling happy! 😊",
            "Your joy is contagious! What's making you feel so good?",
            "I'm glad you're experiencing joy right now!"
        ],
        'sadness': [
            "I'm sorry you're feeling down. 💙",
            "It's okay to feel sad sometimes. I'm here to listen.",
            "Thank you for sharing your feelings. What might help you feel better?"
        ],
        'anger': [
            "I sense you're feeling frustrated. 😐",
            "Anger is a natural emotion. What's triggering these feelings?",
            "Let's try to work through what's making you angry together."
        ],
        'fear': [
            "It sounds like you're feeling anxious. 😟",
            "Fear can be overwhelming. What specifically are you concerned about?",
            "I'm here to help you work through these fears."
        ],
        'surprise': [
            "It seems something surprised you! 😲",
            "Would you like to share what happened?",
            "Surprises can be exciting or unsettling. How are you feeling about it?"
        ],
        'disgust': [
            "I sense some discomfort or dislike. 😣",
            "Would you like to talk about what's bothering you?",
            "Sometimes writing down our thoughts can help process them."
        ],
        'neutral': [
            "Thanks for sharing. 🙂",
            "How are you really feeling today?",
            "I'm here to listen if you'd like to elaborate on your feelings."
        ]
    }
    
    # Select a random response from the appropriate category
    import random
    emotion_responses = responses.get(emotion, responses['neutral'])
    primary_response = random.choice(emotion_responses)
    
    # Create a more detailed response
    if confidence > 0.7:
        confidence_text = f"I'm {confidence*100:.1f}% confident you're feeling {emotion}."
    else:
        confidence_text = f"I think you might be feeling {emotion}, but I'm not entirely sure."
    
    return {
        'primary_response': primary_response,
        'emotion': emotion,
        'confidence': confidence,
        'confidence_text': confidence_text,
        'full_text': f"{primary_response} {confidence_text}"
    }

# Health check endpoint to test connection to Colab API
@app.route('/health', methods=['GET'])
def health_check():
    try:
        response = requests.get(f"{COLAB_API_URL}/predict", timeout=5)
        return jsonify({
            'flask_status': 'running',
            'colab_connection': 'connected' if response.status_code == 405 else 'unexpected_response',
            'colab_status_code': response.status_code
        })
    except Exception as e:
        return jsonify({
            'flask_status': 'running',
            'colab_connection': 'failed',
            'error': str(e)
        })

# Define the route for the main page
@app.route('/')
def home():
    return render_template('index.html')

# Define the route to handle the chat message POST request
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Get the JSON data sent from the frontend
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'response': "Please type a message so I can understand how you're feeling."})
        
        # Preprocess the user's message
        processed_message = preprocess_text(user_message)
        
        # Call your Colab API to get emotion prediction
        emotion_data = call_colab_api(user_message)  # Using original text for better accuracy
        
        if emotion_data and isinstance(emotion_data, list) and len(emotion_data) > 0:
            # Extract emotion and confidence score from the first prediction
            emotion = emotion_data[0].get('label', 'neutral')
            confidence = emotion_data[0].get('score', 0.5)
            
            # Generate a contextual response
            response_data = generate_response(emotion, confidence, user_message)
            
            # Send the response back to the frontend as JSON
            return jsonify({
                'response': response_data['full_text'],
                'emotion': emotion,
                'confidence': confidence,
                'processed_text': processed_message,
                'status': 'success'
            })
        else:
            # Fallback response if API call fails
            return jsonify({
                'response': "I'm having trouble connecting to my emotion detection service right now. Please try again later.",
                'emotion': 'unknown',
                'confidence': 0,
                'processed_text': processed_message,
                'status': 'api_error'
            })
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({
            'response': "Sorry, I encountered an error processing your message.",
            'emotion': 'error',
            'confidence': 0,
            'status': 'error'
        })

if __name__ == '__main__':
    url = "https://9e1b43d3592e.ngrok-free.app/predict"
    print(f"Connecting to Colab API at: {url}")

    app.run(debug=True, port=5001)