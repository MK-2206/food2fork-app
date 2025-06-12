import streamlit as st
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv
import google.generativeai as genai
import hashlib
import pandas as pd
from fpdf import FPDF
import datetime
import uuid
import json
import math
# Load environment variables
load_dotenv()

# Set up Google Gemini API (or use OpenAI if you prefer)
# You'll need to set GEMINI_API_KEY in your .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Set up the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# Set page config
st.set_page_config(
    page_title="Food2Fork - Reduce Waste, Share Extras",
    layout="wide",
    page_icon="🍲",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton>button {
        border-radius: 20px;
        font-weight: bold;
        background-color: #3498db;
        color: white;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .green-button>button {
        background-color: #27ae60;
    }
    .green-button>button:hover {
        background-color: #219955;
    }
    .orange-button>button {
        background-color: #e67e22;
    }
    .orange-button>button:hover {
        background-color: #d35400;
    }
    .stTextArea>div>div>textarea {
        border-radius: 10px;
        border-color: #bdc3c7;
    }
    .stSelectbox>div>div>div {
        border-radius: 10px;
    }
    .stImage {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .recipe-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .listing-card {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 15px;
    border-left: 5px solid #3498db;
}
.listing-card * {
    color: #222222;  /* or try black: #000000 */
}

    .listing-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    .listing-card.expiring-soon {
        border-left: 5px solid #e74c3c;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 5px;
        color: white;
    }
    .badge-vegetarian {
        background-color: #27ae60;
    }
    .badge-vegan {
        background-color: #2ecc71;
    }
    .badge-gluten-free {
        background-color: #f39c12;
    }
    .badge-expiring {
        background-color: #e74c3c;
    }
    .badge-new {
        background-color: #3498db;
    }
    .profile-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 14px;
        font-weight: bold;
        margin-right: 5px;
        color: white;
        background-color: #8e44ad;
    }
    .impact-counter {
        text-align: center;
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .impact-number {
        font-size: 2rem;
        font-weight: bold;
        color: #27ae60;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #3498db20;
        align-items: flex-end;
    }
    .chat-message.bot {
        background-color: #f8f9fa;
        align-items: flex-start;
    }
    .chat-message-content {
        max-width: 80%;
    }
    .expiry-alert {
    background-color: #ffecdb;
    padding: 10px;
    border-radius: 10px;
    border-left: 5px solid #e74c3c;
    margin-bottom: 10px;
    color: #333333; /* Adding darker text color */
    font-weight: 500; /* Making text slightly bolder */
}
    .inventory-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px;
        border-bottom: 1px solid #eee;
    }
    .inventory-item:hover {
        background-color: #f5f5f5;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions
def image_to_bytes(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return buffered.getvalue()

def image_hash(image):
    return hashlib.md5(image_to_bytes(image)).hexdigest()

def is_duplicate(new_image, existing_images):
    new_hash = image_hash(new_image)
    for img in existing_images:
        if image_hash(img) == new_hash:
            return True
    return False

def identify_items(images):
    all_items = []
    for image in images:
        base64_image = base64.b64encode(image_to_bytes(image)).decode('utf-8')

        try:
            response = model.generate_content([
                "List all the food items you can see in this fridge image. Provide the list in a comma-separated format.",
                {"mime_type": "image/jpeg", "data": base64_image}
            ])

            items = response.text.split(',')
            all_items.extend([item.strip() for item in items])
        except Exception as e:
            st.error(f"An error occurred while identifying items: {str(e)}")

    return list(set(all_items))  # Remove duplicates

def generate_recipe(items, diet_preference, cuisine_preference):
    try:
        diet_instruction = f"The recipe should be {diet_preference.lower()}." if diet_preference != "None" else ""
        cuisine_instruction = f"The recipe should be {cuisine_preference} cuisine." if cuisine_preference != "Any" else ""

        prompt = f"Create a recipe using these ingredients: {', '.join(items)}. {diet_instruction} {cuisine_instruction} Provide the recipe name, ingredients with quantities, and step-by-step instructions."

        response = model.generate_content(prompt)

        return response.text
    except Exception as e:
        st.error(f"An error occurred while generating the recipe: {str(e)}")
        return "Unable to generate recipe. Please try again."

def generate_multiple_recipes(items, diet_preference, cuisine_preference, num_recipes):
    recipes = []
    for _ in range(num_recipes):
        recipe = generate_recipe(items, diet_preference, cuisine_preference)
        recipes.append(recipe)
    return recipes

def get_pdf_download_link(recipes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Use a default font
    pdf.set_font("Arial", size=12)

    for i, recipe in enumerate(recipes, 1):
        pdf.cell(200, 10, txt=f"Recipe {i}", ln=True, align="C")
        pdf.multi_cell(0, 10, txt=recipe)
        pdf.ln(10)

    pdf_output = pdf.output(dest="S").encode("latin-1", errors="ignore")
    b64 = base64.b64encode(pdf_output).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="recipes.pdf">Download PDF File</a>'
    return href

def load_mock_data():
    # Mock user data
    if 'users' not in st.session_state:
        st.session_state.users = {
            'user1': {
                'name': 'Alex Johnson',
                'location': {'lat': 40.7128, 'lng': -74.0060},  # NYC
                'zip_code': '10001',
                'badges': ['🥕 Food Saver', '👨‍🍳 Community Chef'],
                'points': 235,
                'food_saved': 12.5,  # kg
                'donations': 3,
                'dietary_preferences': ['vegetarian']
            },
            'user2': {
                'name': 'Sam Wilson',
                'location': {'lat': 40.7282, 'lng': -73.9942},  # A bit away from user1
                'zip_code': '10002',
                'badges': ['🥕 Food Saver'],
                'points': 120,
                'food_saved': 7.2,
                'donations': 1,
                'dietary_preferences': ['vegan', 'gluten-free']
            },
            'user3': {
                'name': 'Jamie Lee',
                'location': {'lat': 40.7421, 'lng': -74.0018},  # Another nearby location
                'zip_code': '10011',
                'badges': ['👨‍🍳 Community Chef', '🌱 Plant Champion'],
                'points': 310,
                'food_saved': 15.8,
                'donations': 5,
                'dietary_preferences': ['vegetarian']
            }
        }
    
    # Mock food listings
    if 'food_listings' not in st.session_state:
        st.session_state.food_listings = [
            {
                'id': str(uuid.uuid4()),
                'user_id': 'user2',
                'title': 'Organic Apples',
                'description': '4 organic apples, freshly picked from my garden',
                'quantity': '4 medium',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
                'dietary_tags': ['vegetarian', 'vegan', 'gluten-free'],
                'location': {'lat': 40.7282, 'lng': -73.9942},
                'zip_code': '10002',
                'pickup_options': ['Pickup', 'Delivery (1 mile radius)'],
                'date_posted': (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'status': 'available',
                'image': None  # In a real app this would be a path or URL
            },
            {
                'id': str(uuid.uuid4()),
                'user_id': 'user3',
                'title': 'Homemade Bread',
                'description': 'Freshly baked sourdough bread, too much for just me!',
                'quantity': '1 loaf',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                'dietary_tags': ['vegetarian'],
                'location': {'lat': 40.7421, 'lng': -74.0018},
                'zip_code': '10011',
                'pickup_options': ['Pickup only'],
                'date_posted': datetime.datetime.now().strftime('%Y-%m-%d'),
                'status': 'available',
                'image': None
            },
            {
                'id': str(uuid.uuid4()),
                'user_id': 'user1',
                'title': 'Extra Bell Peppers',
                'description': '3 bell peppers (1 red, 2 yellow) from my weekly vegetable box',
                'quantity': '3 peppers',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
                'dietary_tags': ['vegetarian', 'vegan', 'gluten-free'],
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'zip_code': '10001',
                'pickup_options': ['Pickup', 'Delivery (2 mile radius)'],
                'date_posted': (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                'status': 'available',
                'image': None
            }
        ]
    
    # Mock inventory data
    if 'user_inventory' not in st.session_state:
        st.session_state.user_inventory = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Milk',
                'quantity': '1 liter',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
                'category': 'Dairy',
                'date_added': (datetime.datetime.now() - datetime.timedelta(days=4)).strftime('%Y-%m-%d')
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Tomatoes',
                'quantity': '4 medium',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
                'category': 'Vegetables',
                'date_added': (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Chicken Breast',
                'quantity': '500g',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'category': 'Meat',
                'date_added': (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Carrots',
                'quantity': '6 medium',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
                'category': 'Vegetables',
                'date_added': (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Yogurt',
                'quantity': '500g',
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
                'category': 'Dairy',
                'date_added': (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
            }
        ]
    
    # Mock chat messages
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = {
            'user2': [
                {'sender': 'user2', 'message': 'Hi, I saw you have some apples available?', 'timestamp': '2023-05-03 14:30:00'},
                {'sender': 'current_user', 'message': 'Yes! They\'re organic and fresh. When would you like to pick them up?', 'timestamp': '2023-05-03 14:35:00'},
                {'sender': 'user2', 'message': 'Could I come by tomorrow around 5pm?', 'timestamp': '2023-05-03 14:40:00'}
            ],
            'user3': [
                {'sender': 'current_user', 'message': 'Hi, is the sourdough bread still available?', 'timestamp': '2023-05-02 10:15:00'},
                {'sender': 'user3', 'message': 'Yes it is! Do you want to pick it up today?', 'timestamp': '2023-05-02 10:20:00'},
                {'sender': 'current_user', 'message': 'That would be great. Is 2pm ok?', 'timestamp': '2023-05-02 10:25:00'},
                {'sender': 'user3', 'message': 'Perfect, see you then!', 'timestamp': '2023-05-02 10:30:00'}
            ]
        }
    
    # Mock NGO data
    if 'ngo_partners' not in st.session_state:
        st.session_state.ngo_partners = [
            {
                'id': 'ngo1',
                'name': 'Food For All',
                'description': 'Collects excess food to distribute to homeless shelters',
                'area': 'New York City',
                'pickup_available': True,
                'min_donation_size': '5 lbs',
                'contact': 'donations@foodforall.org'
            },
            {
                'id': 'ngo2',
                'name': 'Community Kitchen',
                'description': 'Community kitchen preparing meals for those in need',
                'area': 'Brooklyn, Queens',
                'pickup_available': True,
                'min_donation_size': '3 lbs',
                'contact': 'help@communitykitchen.org'
            },
            {
                'id': 'ngo3',
                'name': 'GreenPlate',
                'description': 'Fighting food waste through redistribution',
                'area': 'Manhattan, Bronx',
                'pickup_available': False,
                'min_donation_size': '10 lbs',
                'contact': 'info@greenplate.org'
            }
        ]

# Initialize session state
def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'Home'
    if 'images' not in st.session_state:
        st.session_state.images = []
    if 'ingredients' not in st.session_state:
        st.session_state.ingredients = []
    if 'recipes' not in st.session_state:
        st.session_state.recipes = []
    if 'current_user' not in st.session_state:
        st.session_state.current_user = {
            'name': 'Your Name',
            'location': {'lat': 40.7128, 'lng': -74.0060},  # Default to NYC
            'zip_code': '10001',
            'badges': [],
            'points': 0,
            'food_saved': 0,
            'donations': 0,
            'dietary_preferences': []
        }
    if 'selected_chat_user' not in st.session_state:
        st.session_state.selected_chat_user = None
    if 'new_chat_message' not in st.session_state:
        st.session_state.new_chat_message = ""
    if 'shopping_list' not in st.session_state:
        st.session_state.shopping_list = []
    
    # Load mock data
    load_mock_data()

# Calculate distance between two points
def calculate_distance(loc1, loc2):
    """Calculate distance between two points in miles using the Haversine formula."""
    # Earth radius in miles
    R = 3958.8
    
    # Convert coordinates from degrees to radians
    lat1_rad = math.radians(loc1['lat'])
    lon1_rad = math.radians(loc1['lng'])
    lat2_rad = math.radians(loc2['lat'])
    lon2_rad = math.radians(loc2['lng'])
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance
# Function to add new food listing
def add_food_listing(title, description, quantity, expiry_date, dietary_tags, pickup_options, zip_code, image=None):
    new_listing = {
        'id': str(uuid.uuid4()),
        'user_id': 'current_user',
        'title': title,
        'description': description,
        'quantity': quantity,
        'expiry_date': expiry_date,
        'dietary_tags': dietary_tags,
        'location': st.session_state.current_user['location'],
        'zip_code': zip_code,
        'pickup_options': pickup_options,
        'date_posted': datetime.datetime.now().strftime('%Y-%m-%d'),
        'status': 'available',
        'image': image
    }
    st.session_state.food_listings.append(new_listing)
    
    # Update user stats
    food_weight = 0.5  # Assuming an average weight in kg
    st.session_state.current_user['food_saved'] += food_weight
    st.session_state.current_user['points'] += 10
    
    # Check if user should get new badges
    if st.session_state.current_user['food_saved'] >= 5 and '🥕 Food Saver' not in st.session_state.current_user['badges']:
        st.session_state.current_user['badges'].append('🥕 Food Saver')
    
    return new_listing['id']

# Function to add item to inventory
def add_inventory_item(name, quantity, expiry_date, category):
    new_item = {
        'id': str(uuid.uuid4()),
        'name': name,
        'quantity': quantity,
        'expiry_date': expiry_date,
        'category': category,
        'date_added': datetime.datetime.now().strftime('%Y-%m-%d')
    }
    st.session_state.user_inventory.append(new_item)
    return new_item['id']

# Function to send message
def send_message(recipient_id, message):
    if recipient_id not in st.session_state.chat_messages:
        st.session_state.chat_messages[recipient_id] = []
    
    new_message = {
        'sender': 'current_user',
        'message': message,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    st.session_state.chat_messages[recipient_id].append(new_message)
    st.session_state.new_chat_message = ""

# Function to donate to NGO
def donate_to_ngo(ngo_id, items, quantity):
    # Update user stats
    st.session_state.current_user['donations'] += 1
    st.session_state.current_user['points'] += 25
    
    # Check if user should get new badges
    if st.session_state.current_user['donations'] >= 3 and '❤️ Generous Donor' not in st.session_state.current_user['badges']:
        st.session_state.current_user['badges'].append('❤️ Generous Donor')
    
    # Return success message
    ngo_name = next((ngo['name'] for ngo in st.session_state.ngo_partners if ngo['id'] == ngo_id), "the organization")
    return f"Successfully donated {quantity} of {items} to {ngo_name}!"

# Function to check for expiring items
def get_expiring_items(days_threshold=3):
    expiring_items = []
    current_date = datetime.datetime.now().date()
    
    for item in st.session_state.user_inventory:
        expiry_date = datetime.datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
        days_remaining = (expiry_date - current_date).days
        
        if 0 <= days_remaining <= days_threshold:
            item['days_remaining'] = days_remaining
            expiring_items.append(item)
    
    return expiring_items

# Function to suggest recipes for expiring items
def suggest_recipes_for_expiring(expiring_items):
    if not expiring_items:
        return []
    
    expiring_ingredients = [item['name'] for item in expiring_items]
    try:
        prompt = f"Create a recipe title that uses these ingredients that are about to expire: {', '.join(expiring_ingredients)}. Just provide the title, nothing else."
        response = model.generate_content(prompt)
        recipe_title = response.text.strip()
        
        return {
            'title': recipe_title,
            'ingredients': expiring_ingredients
        }
    except Exception as e:
        st.error(f"An error occurred while generating recipe suggestion: {str(e)}")
        return {
            'title': f"Recipe using {expiring_ingredients[0]}",
            'ingredients': expiring_ingredients
        }

# Function to generate shopping list based on inventory
def generate_shopping_list():
    # Get categories we're low on
    categories_count = {}
    for item in st.session_state.user_inventory:
        category = item['category']
        if category not in categories_count:
            categories_count[category] = 0
        categories_count[category] += 1
    
    # Determine what we need more of
    shopping_list = []
    
    # Basic categories to always have
    essential_categories = {
        'Vegetables': 5,
        'Fruits': 3,
        'Dairy': 2,
        'Protein': 2,
        'Grains': 2
    }
    
    for category, min_count in essential_categories.items():
        current_count = categories_count.get(category, 0)
        if current_count < min_count:
            # Suggest specific items for each category
            if category == 'Vegetables':
                shopping_list.append({'category': category, 'items': ['Carrots', 'Broccoli', 'Spinach']})
            elif category == 'Fruits':
                shopping_list.append({'category': category, 'items': ['Apples', 'Bananas', 'Berries']})
            elif category == 'Dairy':
                shopping_list.append({'category': category, 'items': ['Milk', 'Yogurt', 'Cheese']})
            elif category == 'Protein':
                shopping_list.append({'category': category, 'items': ['Chicken', 'Eggs', 'Tofu']})
            elif category == 'Grains':
                shopping_list.append({'category': category, 'items': ['Rice', 'Pasta', 'Bread']})
    
    return shopping_list

# Home Page
def home_page():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("🍲 FoodSaver - Reduce Waste, Share Food 🍲")
        st.markdown("""
        Welcome to FoodSaver! This app helps you reduce food waste by:

        * **Creating recipes** from your fridge contents
        * **Sharing extra ingredients** with neighbors
        * **Tracking expiration dates** to use food before it spoils
        * **Connecting with your community** through food sharing
        * **Contributing to food waste reduction** with real impact metrics
        
        Get started by exploring the features in the sidebar!
        """)
        
        # Quick actions
        st.subheader("Quick Actions")
        cols = st.columns(3)
        with cols[0]:
            if st.button("📸 Scan My Fridge", use_container_width=True):
                st.session_state.page = 'Recipe Finder'
                st.rerun()
        with cols[1]:
            if st.button("🛒 Track Inventory", use_container_width=True):
                st.session_state.page = 'Inventory'
                st.rerun()
        with cols[2]:
            if st.button("📦 Share Extras", use_container_width=True):
                st.session_state.page = 'Share Marketplace'
                st.rerun()
                
        # Show expiring items alert
        expiring_items = get_expiring_items()
        if expiring_items:
            st.markdown("### ⚠️ Items Expiring Soon")
            for item in expiring_items:
                st.markdown(f"""
                <div class="expiry-alert">
                    <strong>{item['name']}</strong> ({item['quantity']}) expires in {item['days_remaining']} days!
                </div>
                """, unsafe_allow_html=True)
            
            

# Recipe Finder Page (Enhanced version of the original app)
def recipe_finder_page():
    st.title("📸 Recipe Finder")
    st.markdown("Take pictures of your fridge contents and get recipe ideas!")
    
    # Step 1: Upload Images
    st.header("Step 1: Upload Fridge Images")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        image_option = st.radio("Choose an option:", ("Upload Images", "Take Pictures"), horizontal=True)
        
        if image_option == "Take Pictures":
            camera_image = st.camera_input("📷 Take a picture of your fridge contents")
            if camera_image:
                new_image = Image.open(camera_image)
                if not is_duplicate(new_image, st.session_state.images):
                    st.session_state.images.append(new_image)
                    st.success("Image added successfully! 🎉")
                else:
                    st.warning("This image is a duplicate and was not added.")
        else:
            uploaded_files = st.file_uploader("📤 Upload fridge images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            if uploaded_files:
                new_images = 0
                duplicates = 0
                for uploaded_file in uploaded_files:
                    new_image = Image.open(uploaded_file)
                    if not is_duplicate(new_image, st.session_state.images):
                        st.session_state.images.append(new_image)
                        new_images += 1
                    else:
                        duplicates += 1
                
                if new_images > 0:
                    st.success(f"{new_images} new image(s) added successfully! 🎉")
                if duplicates > 0:
                    st.info(f"{duplicates} duplicate image(s) were not added.")
    
    with col2:
        if st.session_state.images:
            st.subheader("Uploaded Images")
            cols = st.columns(2)
            for i, img in enumerate(st.session_state.images):
                cols[i % 2].image(img, caption=f'Image {i+1}', use_column_width=True)
            
            if st.button('🗑️ Clear All Images', use_container_width=True):
                st.session_state.images = []
                st.rerun()
    
    # Step 2: Identify Ingredients
    st.header("Step 2: Identify Ingredients")
    if st.session_state.images:
        if st.button('🔍 Identify Ingredients', use_container_width=True):
            with st.spinner('Analyzing fridge contents... 🕵️‍♂️'):
                identified_items = identify_items(st.session_state.images)
                st.session_state.ingredients = identified_items
    
    if 'ingredients' in st.session_state and st.session_state.ingredients:
        st.subheader("Identified Ingredients")
        ingredients = st.text_area("✏️ Edit, add, or remove ingredients:",
                                  value='\n'.join(st.session_state.ingredients),
                                  height=150,
                                  help="Each ingredient should be on a new line.")
        st.session_state.ingredients = [item.strip() for item in ingredients.split('\n') if item.strip()]
        
        # Add these ingredients to inventory option
        if st.button("📥 Add These Ingredients to Inventory", use_container_width=True):
            for ingredient in st.session_state.ingredients:
                add_inventory_item(
                    name=ingredient,
                    quantity="1 unit",  # Default quantity
                    expiry_date=(datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),  # Default expiry
                    category="Other"  # Default category
                )
            st.success("Ingredients added to inventory!")
    
    # Step 3: Generate Recipe
    st.header("Step 3: Generate Recipe")
    if 'ingredients' in st.session_state and st.session_state.ingredients:
        st.subheader("Recipe Preferences")
        col1, col2, col3 = st.columns(3)
        with col1:
            diet_options = ["None", "Vegetarian", "Vegan", "Gluten-Free", "Keto", "Low-Carb", "Paleo"]
            diet_preference = st.selectbox("🥗 Select dietary preference:", diet_options)
        with col2:
            cuisine_options = ["Any", "Italian", "Mexican", "Asian", "Mediterranean", "American", "Indian", "French"]
            cuisine_preference = st.selectbox("🌍 Select cuisine preference:", cuisine_options)
        with col3:
            num_recipes = st.slider("🔢 Number of recipes:", min_value=1, max_value=5, value=1)
        
        if st.button('🧑‍🍳 Generate Recipes', use_container_width=True):
            with st.spinner(f'Crafting your {num_recipes} recipe(s)... 👨‍🍳'):
                recipes = generate_multiple_recipes(st.session_state.ingredients, diet_preference, cuisine_preference, num_recipes)
                st.session_state.recipes = recipes
        
        if 'recipes' in st.session_state and st.session_state.recipes:
            st.subheader("Your Recipes")
            for i, recipe in enumerate(st.session_state.recipes, 1):
                st.markdown(f'<div class="recipe-container"><h3>Recipe {i}</h3>{recipe}</div>', unsafe_allow_html=True)
            
            # Provide download link
            st.markdown(get_pdf_download_link(st.session_state.recipes), unsafe_allow_html=True)
            
            # Share excess ingredients option
            unused_ingredients = []
            for ingredient in st.session_state.ingredients:
                found = False
                for recipe in st.session_state.recipes:
                    if ingredient.lower() in recipe.lower():
                        found = True
                        break
                if not found:
                    unused_ingredients.append(ingredient)
            
            if unused_ingredients:
                st.markdown("### Unused Ingredients")
                st.markdown("Would you like to share these unused ingredients with your community?")
                st.write(", ".join(unused_ingredients))
                
                if st.button("📦 Share Unused Ingredients", use_container_width=True):
                    st.session_state.page = 'Share Marketplace'
                    st.session_state.share_ingredients = unused_ingredients
                    st.rerun()

# Share Marketplace Page
def share_marketplace_page():
    st.title("📦 Share Your Extras Marketplace")
    st.markdown("Post your leftover food items or find ingredients from neighbors!")
    
    tab1, tab2 = st.tabs(["🔍 Find Items", "📤 Share Items"])
    
    with tab1:
        st.subheader("Find Shared Items")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            zip_filter = st.text_input("🏙️ ZIP Code:", value=st.session_state.current_user['zip_code'])
        with col2:
            distance_filter = st.slider("📍 Max Distance (miles):", min_value=1, max_value=20, value=5)
        with col3:
            dietary_filter = st.multiselect("🥗 Dietary Preferences:", 
                                            ["Vegetarian", "Vegan", "Gluten-Free"],
                                            default=st.session_state.current_user.get('dietary_preferences', []))
        
        # Filter listings
        filtered_listings = []
        for listing in st.session_state.food_listings:
            # Skip user's own listings
            if listing['user_id'] == 'current_user':
                continue
            
            # Apply filters
            distance = 0  # Default for same zip
            if listing['zip_code'] != zip_filter:
                user_loc = st.session_state.current_user['location']
                listing_loc = listing['location']
                distance = calculate_distance(user_loc, listing_loc)
                if distance > distance_filter:
                    continue
            
            # Dietary filter
            if dietary_filter:
                if not any(tag in listing['dietary_tags'] for tag in [d.lower() for d in dietary_filter]):
                    continue
            
            # Add distance to listing
            listing_copy = listing.copy()
            listing_copy['distance'] = distance
            filtered_listings.append(listing_copy)
        
        # Sort by distance
        filtered_listings.sort(key=lambda x: x['distance'])
        
        # Display results
        if filtered_listings:
            st.subheader(f"Found {len(filtered_listings)} items near you")
            
            for listing in filtered_listings:
                user = st.session_state.users.get(listing['user_id'], {'name': 'Unknown User'})
                days_to_expiry = (datetime.datetime.strptime(listing['expiry_date'], '%Y-%m-%d').date() - 
                                  datetime.datetime.now().date()).days
                
                expiry_class = " expiring-soon" if days_to_expiry <= 3 else ""
                
                st.markdown(f"""
                <div class="listing-card{expiry_class}">
                    <h4>{listing['title']}</h4>
                    <p>{listing['description']}</p>
                    <p><strong>Quantity:</strong> {listing['quantity']}</p>
                    <p><strong>Expires in:</strong> {days_to_expiry} days</p>
                    <p><strong>From:</strong> {user['name']} ({listing['zip_code']})</p>
                    <p><strong>Distance:</strong> {listing['distance']:.1f} miles</p>
                    <p><strong>Pickup options:</strong> {', '.join(listing['pickup_options'])}</p>
                    <div>
                """, unsafe_allow_html=True)
                
                # Display dietary tags
                tags_html = ""
                for tag in listing['dietary_tags']:
                    tag_class = f"badge-{tag.lower()}"
                    tags_html += f'<span class="badge {tag_class}">{tag.upper()}</span>'
                st.markdown(tags_html, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Contact button
                if st.button(f"Contact about {listing['title']}", key=f"contact_{listing['id']}", use_container_width=True):
                    st.session_state.page = 'Chat'
                    st.session_state.selected_chat_user = listing['user_id']
                    st.rerun()
        else:
            st.info("No matching items found. Try adjusting your filters!")
    
    with tab2:
        st.subheader("Share Your Extra Items")
        
        # Check if there are ingredients to share from the recipe finder
        share_ingredients = st.session_state.get('share_ingredients', [])
        
        with st.form("share_form"):
            st.markdown("Enter the details of the food item you want to share:")
            
            title = st.text_input("Title:", value="" if not share_ingredients else f"Extra {', '.join(share_ingredients[:2])}")
            
            description = st.text_area("Description:", 
                                     value="" if not share_ingredients else f"Sharing extra ingredients I won't use: {', '.join(share_ingredients)}")
            
            quantity = st.text_input("Quantity:", value="")
            
            expiry_date = st.date_input("Expiry Date:", 
                                       value=datetime.datetime.now().date() + datetime.timedelta(days=7))
            
            dietary_tags = st.multiselect("Dietary Tags:", 
                                        ["Vegetarian", "Vegan", "Gluten-Free"],
                                        default=[])
            
            pickup_options = st.multiselect("Pickup Options:", 
                                          ["Pickup", "Delivery (1 mile radius)", "Delivery (3 mile radius)"],
                                          default=["Pickup"])
            
            zip_code = st.text_input("ZIP Code:", value=st.session_state.current_user['zip_code'])
            
            upload_image = st.file_uploader("Upload Image (Optional):", type=["jpg", "jpeg", "png"])
            
            # Option to donate to charity
            st.markdown("### 🤝 Charity Option")
            donate_to_charity = st.checkbox("Offer this item to local food banks/charities")
            
            if donate_to_charity:
                selected_ngo = st.selectbox("Select Organization:", 
                                          [ngo['name'] for ngo in st.session_state.ngo_partners],
                                          index=0)
            
            submitted = st.form_submit_button("📤 Share Item")
            
            if submitted:
                if not title or not description or not quantity:
                    st.error("Please fill out all required fields!")
                else:
                    # Process image if uploaded
                    image = None
                    if upload_image:
                        image = Image.open(upload_image)
                    
                    # Create the listing
                    listing_id = add_food_listing(
                        title=title,
                        description=description,
                        quantity=quantity,
                        expiry_date=expiry_date.strftime('%Y-%m-%d'),
                        dietary_tags=[tag.lower() for tag in dietary_tags],
                        pickup_options=pickup_options,
                        zip_code=zip_code,
                        image=image
                    )
                    
                    # Handle charity donation if selected
                    donation_message = ""
                    if donate_to_charity:
                        ngo_id = next((ngo['id'] for ngo in st.session_state.ngo_partners 
                                      if ngo['name'] == selected_ngo), None)
                        if ngo_id:
                            donation_message = donate_to_ngo(ngo_id, title, quantity)
                    
                    success_message = f"🎉 Your item has been shared successfully!"
                    if donation_message:
                        success_message += f" {donation_message}"
                    
                    st.success(success_message)
                    
                    # Clear the share_ingredients from session state
                    if 'share_ingredients' in st.session_state:
                        del st.session_state['share_ingredients']
                    
                    # Add badge if first time sharing
                    if '👨‍🍳 Community Chef' not in st.session_state.current_user['badges']:
                        st.session_state.current_user['badges'].append('👨‍🍳 Community Chef')
                        st.balloons()
                        st.markdown("### 🏆 New Badge Earned: 👨‍🍳 Community Chef")

# Inventory Page
def inventory_page():
    st.title("🛒 Inventory & Grocery Planning")
    st.markdown("Track your food inventory, get expiry alerts, and plan your grocery shopping!")
    
    tab1, tab2, tab3 = st.tabs(["📋 My Inventory", "⚠️ Expiry Alerts", "🛍️ Shopping List"])
    
    with tab1:
        st.subheader("Current Inventory")
        
        # Add new item form
        with st.expander("➕ Add New Item"):
            with st.form("add_inventory_item"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Item Name:")
                    quantity = st.text_input("Quantity:")
                with col2:
                    category = st.selectbox("Category:", ["Vegetables", "Fruits", "Dairy", "Meat", "Grains", "Other"])
                    expiry_date = st.date_input("Expiry Date:", value=datetime.datetime.now().date() + datetime.timedelta(days=7))
                
                submitted = st.form_submit_button("Add Item")
                if submitted:
                    if name and quantity:
                        add_inventory_item(name, quantity, expiry_date.strftime('%Y-%m-%d'), category)
                        st.success(f"Added {name} to inventory!")
                        st.rerun()
                    else:
                        st.error("Please fill out all fields")
        
        # Filter inventory
        filter_category = st.selectbox("Filter by Category:", ["All"] + list(set([item['category'] for item in st.session_state.user_inventory])))
        
        # Sort inventory
        sort_option = st.radio("Sort by:", ["Expiry Date", "Name", "Category"], horizontal=True)
        
        # Process inventory
        inventory = st.session_state.user_inventory.copy()
        
        # Apply filter
        if filter_category != "All":
            inventory = [item for item in inventory if item['category'] == filter_category]
        
        # Apply sort
        if sort_option == "Expiry Date":
            inventory.sort(key=lambda x: x['expiry_date'])
        elif sort_option == "Name":
            inventory.sort(key=lambda x: x['name'])
        elif sort_option == "Category":
            inventory.sort(key=lambda x: x['category'])
        
        # Display inventory
        current_date = datetime.datetime.now().date()
        for item in inventory:
            expiry_date = datetime.datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
            days_remaining = (expiry_date - current_date).days
            
            expiry_class = ""
            if days_remaining <= 0:
                expiry_status = "❌ Expired"
                expiry_class = "expiring-soon"
            elif days_remaining <= 3:
                expiry_status = f"⚠️ Expires in {days_remaining} days"
                expiry_class = "expiring-soon"
            else:
                expiry_status = f"✅ Expires in {days_remaining} days"
            
            st.markdown(f"""
            <div class="inventory-item {expiry_class}">
                <div>
                    <strong>{item['name']}</strong> - {item['quantity']} ({item['category']})
                </div>
                <div>
                    {expiry_status}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # No items message
        if not inventory:
            st.info("No items in inventory. Add some items to get started!")
    
    with tab2:
        st.subheader("Expiry Alerts")
        
        # Get expiring items
        expiring_soon = get_expiring_items(days_threshold=5)
        
        if expiring_soon:
            st.markdown("### Items Expiring Soon")
            
            for item in expiring_soon:
                st.markdown(f"""
                <div class="expiry-alert">
                    <strong>{item['name']}</strong> ({item['quantity']}) expires in {item['days_remaining']} days!
                </div>
                """, unsafe_allow_html=True)
            
            # Recipe suggestions
            st.markdown("### 💡 Recipe Suggestions")
            st.markdown("Here are some recipes to help you use up these ingredients:")
            
            if st.button("Generate Recipes for Expiring Items", use_container_width=True):
                with st.spinner("Generating recipes..."):
                    expiring_ingredients = [item['name'] for item in expiring_soon]
                    recipes = generate_multiple_recipes(expiring_ingredients, "None", "Any", 2)
                    
                    for i, recipe in enumerate(recipes, 1):
                        st.markdown(f'<div class="recipe-container"><h3>Recipe {i}</h3>{recipe}</div>', unsafe_allow_html=True)
            
            # Share option
            st.markdown("### 📦 Share Option")
            st.markdown("Can't use these items before they expire? Share them with your community!")
            
            if st.button("Share Expiring Items", use_container_width=True):
                st.session_state.page = 'Share Marketplace'
                st.session_state.share_ingredients = [item['name'] for item in expiring_soon]
                st.rerun()
        else:
            st.success("Great job! No items are expiring soon.")
    
    with tab3:
        st.subheader("Shopping List Generator")
        st.markdown("Get smart shopping recommendations based on your current inventory and meal plans.")
        
        # Generate shopping list
        shopping_list = generate_shopping_list()
        
        if shopping_list:
            st.markdown("### Recommended Shopping List")
            st.markdown("Based on your current inventory, we recommend getting:")
            
            for category in shopping_list:
                st.markdown(f"#### {category['category']}")
                for item in category['items']:
                    st.markdown(f"- [ ] {item}")
            
            if st.button("Save Shopping List", use_container_width=True):
                st.session_state.shopping_list = shopping_list
                st.success("Shopping list saved!")
        else:
            st.info("Your inventory looks well-stocked! No shopping recommendations at the moment.")
        
        # Manual shopping list
        st.markdown("### Custom Shopping List")
        
        with st.form("manual_shopping_list"):
            shopping_items = st.text_area("Enter items (one per line):")
            submitted = st.form_submit_button("Add to Shopping List")
            
            if submitted and shopping_items:
                items = [item.strip() for item in shopping_items.split('\n') if item.strip()]
                if 'shopping_list' not in st.session_state:
                    st.session_state.shopping_list = []
                
                if not any(d.get('category') == 'Custom' for d in st.session_state.shopping_list):
                    st.session_state.shopping_list.append({'category': 'Custom', 'items': items})
                else:
                    for category in st.session_state.shopping_list:
                        if category['category'] == 'Custom':
                            category['items'].extend(items)
                
                st.success("Items added to shopping list!")

# Friend Connect Page
def friend_connect_page():
    st.title("👥 Local Connect")
    st.markdown("Find and connect with food-sharing neighbors in your area!")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        distance_filter = st.slider("📍 Search Radius (miles):", min_value=1, max_value=20, value=5)
    with col2:
        dietary_filter = st.multiselect("🥗 Dietary Preferences:", 
                                       ["Vegetarian", "Vegan", "Gluten-Free"],
                                       default=[])
    
    # Find nearby users
    nearby_users = []
    for user_id, user in st.session_state.users.items():
        # Skip current user
        if user_id == 'current_user':
            continue
        
        # Calculate distance
        distance = calculate_distance(st.session_state.current_user['location'], user['location'])
        
        # Apply distance filter
        if distance <= distance_filter:
            # Apply dietary filter
            if dietary_filter and not any(pref in user.get('dietary_preferences', []) for pref in dietary_filter):
                continue
            
            # Add distance to user
            user_copy = user.copy()
            user_copy['id'] = user_id
            user_copy['distance'] = distance
            nearby_users.append(user_copy)
    
    # Sort by distance
    nearby_users.sort(key=lambda x: x['distance'])
    
    # Display results
    if nearby_users:
        st.subheader(f"Found {len(nearby_users)} neighbors near you")
        
        for user in nearby_users:
            # User card
            st.markdown(f"""
            <div class="listing-card">
                <h4>{user['name']}</h4>
                <p><strong>Distance:</strong> {user['distance']:.1f} miles</p>
                <p><strong>Food saved:</strong> {user['food_saved']:.1f} kg</p>
            """, unsafe_allow_html=True)
            
            # Badges
            if user.get('badges'):
                badges_html = ""
                for badge in user['badges']:
                    badges_html += f'<span class="profile-badge">{badge}</span>'
                st.markdown(badges_html, unsafe_allow_html=True)
            
            # Dietary preferences
            if user.get('dietary_preferences'):
                tags_html = ""
                for pref in user['dietary_preferences']:
                    tag_class = f"badge-{pref.lower()}"
                    tags_html += f'<span class="badge {tag_class}">{pref.upper()}</span>'
                st.markdown(tags_html, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Contact button
            if st.button(f"Message {user['name']}", key=f"msg_{user['id']}", use_container_width=True):
                st.session_state.page = 'Chat'
                st.session_state.selected_chat_user = user['id']
                st.rerun()
    else:
        st.info("No neighbors found with the current filters. Try expanding your search radius!")

# Chat Page
def chat_page():
    st.title("💬 Chat")
    
    # Sidebar with chat list
    with st.sidebar:
        st.subheader("Conversations")
        
        chats = []
        for user_id, messages in st.session_state.chat_messages.items():
            user = st.session_state.users.get(user_id, {'name': 'Unknown User'})
            last_message = messages[-1]['message'] if messages else ""
            chats.append((user_id, user['name'], last_message))
        
        for user_id, name, last_message in chats:
            if st.button(f"{name}: {last_message[:20]}...", key=f"chat_{user_id}", use_container_width=True):
                st.session_state.selected_chat_user = user_id
                st.rerun()
    
    # Main chat area
    if st.session_state.selected_chat_user:
        user_id = st.session_state.selected_chat_user
        user = st.session_state.users.get(user_id, {'name': 'Unknown User'})
        
        st.subheader(f"Chat with {user['name']}")
        
        # Display messages
        messages = st.session_state.chat_messages.get(user_id, [])
        
        for message in messages:
            if message['sender'] == 'current_user':
                st.markdown(f"""
                <div class="chat-message user">
                    <div>You</div>
                    <div class="chat-message-content">{message['message']}</div>
                    <small>{message['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot">
                    <div>{user['name']}</div>
                    <div class="chat-message-content">{message['message']}</div>
                    <small>{message['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Message input
        with st.form("send_message_form"):
            st.session_state.new_chat_message = st.text_area("Type your message:", value=st.session_state.new_chat_message)
            submitted = st.form_submit_button("Send")
            
            if submitted and st.session_state.new_chat_message:
                send_message(user_id, st.session_state.new_chat_message)
                st.rerun()
    else:
        st.info("Select a conversation from the sidebar or start a new chat from the marketplace.")

# Impact Tracker Page
def impact_tracker_page():
    st.title("🏆 Impact Tracker & Community Leaderboard")
    st.markdown("Track your food waste reduction impact and see how you compare to the community!")
    
    # User's impact stats
    st.header("Your Impact")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="impact-counter">
            <div class="impact-number">{st.session_state.current_user['food_saved']:.1f}</div>
            <div>kg of food saved</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="impact-counter">
            <div class="impact-number">{st.session_state.current_user['points']}</div>
            <div>points earned</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="impact-counter">
            <div class="impact-number">{st.session_state.current_user['donations']}</div>
            <div>donations made</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Badges showcase
    st.subheader("Your Badges")
    if st.session_state.current_user['badges']:
        badges_html = ""
        for badge in st.session_state.current_user['badges']:
            badges_html += f'<span class="profile-badge">{badge}</span>'
        st.markdown(badges_html, unsafe_allow_html=True)
        
        # Badge descriptions
        st.markdown("""
        **Badge Meanings:**
        - 🥕 **Food Saver**: Saved at least 5kg of food from waste
        - 👨‍🍳 **Community Chef**: Shared food items with your community
        - ❤️ **Generous Donor**: Made at least 3 donations to food banks
        - 🌱 **Plant Champion**: Primarily shares plant-based foods
        """)
    else:
        st.info("You haven't earned any badges yet. Start sharing food to earn your first badge!")
    
    # Community leaderboard
    st.header("Community Leaderboard")
    
    # Combine current user and other users
    all_users = list(st.session_state.users.values())
    all_users.append(st.session_state.current_user)
    
    # Sort by points
    all_users.sort(key=lambda x: x['points'], reverse=True)
    
    # Add rank
    for i, user in enumerate(all_users, 1):
        user['rank'] = i
    
    # Display leaderboard
    for user in all_users:
        is_current = user['name'] == st.session_state.current_user['name']
        row_style = "background-color: #e3f2fd;" if is_current else ""
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; margin-bottom: 5px; border-radius: 5px; {row_style}">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 1.2rem; font-weight: bold; width: 30px;">{user['rank']}</div>
                <div>
                    <div style="font-weight: bold;">{user['name']} {' (You)' if is_current else ''}</div>
                    <div style="font-size: 0.8rem;">Food saved: {user['food_saved']:.1f} kg</div>
                </div>
            </div>
            <div style="font-weight: bold; font-size: 1.2rem;">{user['points']} pts</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Community total impact
    st.header("Community Total Impact")
    
    total_food_saved = sum(user['food_saved'] for user in all_users)
    total_donations = sum(user['donations'] for user in all_users)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="impact-counter">
            <div class="impact-number">{total_food_saved:.1f}</div>
            <div>kg of food saved</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="impact-counter">
            <div class="impact-number">{total_donations}</div>
            <div>charity donations</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Environmental impact
    st.subheader("Environmental Impact")
    st.markdown(f"""
    By saving {total_food_saved:.1f} kg of food from going to waste, your community has:
    
    - Prevented approximately {(total_food_saved * 2.5):.1f} kg of CO2 emissions
    - Saved around {(total_food_saved * 1000):.0f} liters of water
    - Preserved {(total_food_saved * 0.3):.1f} m² of land from being used for food production
    """)

# NGO Integration Page
def ngo_page():
    st.title("🤝 Charity & NGO Integration")
    st.markdown("Connect with food banks and charitable organizations to donate excess food.")
    
    # List NGO partners
    st.subheader("Our NGO Partners")
    
    for ngo in st.session_state.ngo_partners:
        st.markdown(f"""
        <div class="listing-card">
            <h4>{ngo['name']}</h4>
            <p>{ngo['description']}</p>
            <p><strong>Service Area:</strong> {ngo['area']}</p>
            <p><strong>Pickup Available:</strong> {'Yes' if ngo['pickup_available'] else 'No'}</p>
            <p><strong>Minimum Donation Size:</strong> {ngo['min_donation_size']}</p>
            <p><strong>Contact:</strong> {ngo['contact']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Make a donation
    st.header("Make a Donation")
    
    with st.form("donate_form"):
        st.markdown("Fill out this form to arrange a food donation:")
        
        selected_ngo = st.selectbox("Select Organization:", 
                                  [ngo['name'] for ngo in st.session_state.ngo_partners],
                                  index=0)
        
        items = st.text_area("Items to Donate:", 
                           placeholder="Example: 5 cans of soup, 2 loaves of bread...")
        
        quantity = st.text_input("Approximate Total Quantity:", 
                               placeholder="Example: 10 lbs, 5 kg...")
        
        pickup_needed = st.checkbox("I need the organization to pick up the donation")
        
        if pickup_needed:
            pickup_date = st.date_input("Preferred Pickup Date:", 
                                      value=datetime.datetime.now().date() + datetime.timedelta(days=1))
            pickup_time = st.time_input("Preferred Pickup Time:", 
                                      value=datetime.time(10, 0))
        
        submitted = st.form_submit_button("Submit Donation Request")
        
        if submitted:
            if not items or not quantity:
                st.error("Please fill out all required fields!")
            else:
                # Find the selected NGO
                ngo_id = next((ngo['id'] for ngo in st.session_state.ngo_partners 
                              if ngo['name'] == selected_ngo), None)
                
                if ngo_id:
                    success_message = donate_to_ngo(ngo_id, items, quantity)
                    st.success(success_message)
                    
                    if '❤️ Generous Donor' in st.session_state.current_user['badges']:
                        st.balloons()
                    
                    # Provide next steps
                    st.markdown(f"""
                    ### Next Steps
                    
                    1. You'll receive a confirmation email shortly
                    2. The organization will contact you to finalize details
                    3. {"They will arrange pickup on " + pickup_date.strftime('%Y-%m-%d') + " at " + pickup_time.strftime('%H:%M') if pickup_needed else "Please drop off your donation at their location"}
                    
                    Thank you for your generosity!
                    """)

# Settings Page
def settings_page():
    st.title("⚙️ Settings")
    st.markdown("Configure your profile and app preferences")
    
    tab1, tab2 = st.tabs(["👤 Profile", "🔔 Notifications"])
    
    with tab1:
        st.subheader("Your Profile")
        
        with st.form("profile_form"):
            name = st.text_input("Name:", value=st.session_state.current_user['name'])
            
            zip_code = st.text_input("ZIP Code:", value=st.session_state.current_user['zip_code'])
            
            dietary_preferences = st.multiselect("Dietary Preferences:", 
                                              ["Vegetarian", "Vegan", "Gluten-Free", "Keto", "Paleo"],
                                              default=st.session_state.current_user.get('dietary_preferences', []))
            
            submitted = st.form_submit_button("Save Profile")
            
            if submitted:
                st.session_state.current_user['name'] = name
                st.session_state.current_user['zip_code'] = zip_code
                st.session_state.current_user['dietary_preferences'] = dietary_preferences
                st.success("Profile updated successfully!")
    
    with tab2:
        st.subheader("Notification Settings")
        
        expiry_days = st.slider("Notify me about expiring items __ days in advance:", 
                              min_value=1, max_value=7, value=3)
        
        notify_new_messages = st.checkbox("Notify me about new messages", value=True)
        
        notify_nearby_listings = st.checkbox("Notify me about new food listings in my area", value=True)
        
        if st.button("Save Notification Settings", use_container_width=True):
            st.success("Notification settings saved!")

def main():
    # Initialize session state
    init_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("FoodSaver")
        st.markdown(f"Welcome, {st.session_state.current_user['name']}!")
        
        # Display badges if any
        if st.session_state.current_user['badges']:
            badges_html = ""
            for badge in st.session_state.current_user['badges']:
                badges_html += f'<span class="profile-badge">{badge}</span>'
            st.markdown(badges_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        pages = {
            "Home": "🏠",
            "Recipe Finder": "📸",
            "Share Marketplace": "📦",
            "Inventory": "🛒",
            "Local Connect": "👥",
            "Chat": "💬",
            "Impact Tracker": "🏆",
            "Charity Connect": "🤝",
            "Settings": "⚙️"
        }
        
        for page_name, icon in pages.items():
            if st.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state.page = page_name
                st.rerun()
        
        st.markdown("---")
        st.markdown("Created with ❤️ using Streamlit")
    
    # Main content based on current page
    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Recipe Finder":
        recipe_finder_page()
    elif st.session_state.page == "Share Marketplace":
        share_marketplace_page()
    elif st.session_state.page == "Inventory":
        inventory_page()
    elif st.session_state.page == "Local Connect":
        friend_connect_page()
    elif st.session_state.page == "Chat":
        chat_page()
    elif st.session_state.page == "Impact Tracker":
        impact_tracker_page()
    elif st.session_state.page == "Charity Connect":
        ngo_page()
    elif st.session_state.page == "Settings":
        settings_page()

if __name__ == "__main__":
    main()
   
    
   