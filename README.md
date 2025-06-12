# FridgeFusion 🍳🥗 - Your Smart Kitchen Assistant

**FridgeFusion** is an AI-powered Streamlit web app built by **Mansi Kharke**, designed to help reduce food waste by turning your fridge contents into creative, personalized recipes! 🚀 Whether you're meal prepping or just trying to use what's left before it expires, FridgeFusion has you covered.

## 🌟 Overview

FridgeFusion empowers users to effortlessly convert leftover ingredients into customized, delicious meals. With the help of Google Gemini's AI and a clean, interactive UI, the app helps reduce food waste while promoting sustainable cooking habits. 🌿♻️

## 🔥 Key Features

- 📸 **AI-Based Ingredient Recognition**: Upload fridge photos to auto-identify ingredients using Google Gemini
- 🍽️ **Customized Recipe Generation**: Personalized recipes based on your ingredients and dietary preferences
- 🍱 **Multiple Recipe Suggestions**: Generate and browse through multiple recipe ideas
- 🥗 **Diet-Aware Options**: Filter recipes by vegetarian, vegan, gluten-free, keto, and more
- 📄 **PDF Export**: Download generated recipes as a PDF for offline use
- 📦 **Inventory & Sharing System**: Track expiring items, share food with neighbors, or donate to local NGOs
- 💬 **Real-Time Chat**: Connect with nearby users about shared ingredients
- 🏆 **Impact Dashboard**: See your contributions to food-saving efforts with badges and stats

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- Streamlit
- Pillow
- python-dotenv
- google-generativeai
- fpdf
- pandas

### Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/MK-2206/food2fork-app.git
    cd food2fork-app
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Windows: venv\Scripts\activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up Gemini API key:**
    - Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey)
    - Create a `.env` file in the project root:
      ```env
      GEMINI_API_KEY=your_api_key_here
      ```

5. **Run the app:**
    ```bash
    streamlit run app.py
    ```

6. **To deactivate:**
    ```bash
    deactivate
    ```

## 🚀 How to Use

1. Upload images of your fridge items or take a live picture
2. Let the AI detect ingredients and edit them if needed
3. Select dietary and cuisine preferences
4. Generate recipes
5. Download them or share unused items via the community marketplace

## 📸 Sample Screens

### 🏠 Home Page
![Home Page](assets/Screenshot%202025-06-12%20at%206.17.45%20PM.png)

### 🍽️ Recipe Finder
![Recipe Finder](assets/Screenshot%202025-06-12%20at%206.18.13%20PM.png)

### 📦 Share Marketplace
![Share Marketplace](assets/Screenshot%202025-06-12%20at%206.18.28%20PM.png)

### 🛒 Inventory Tracker
![Inventory](assets/Screenshot%202025-06-12%20at%206.18.35%20PM.png)

### 👥 Local Connect
![Local Connect](assets/Screenshot%202025-06-12%20at%206.19.00%20PM.png)

### 💬 Chat Feature
![Chat](assets/Screenshot%202025-06-12%20at%206.19.09%20PM.png)

### 🏆 Impact Tracker
![Impact Tracker](assets/Screenshot%202025-06-12%20at%206.19.48%20PM.png)


## 🙋‍♀️ About the Developer

Built with ❤️ by **Mansi Kharke**, a full-stack developer passionate about AI, sustainability, and building impact-driven products.

- 💼 LinkedIn: [linkedin.com/in/mansi-kharke-3b7565183](https://www.linkedin.com/in/mansi-kharke-3b7565183)
- 🐙 GitHub: [github.com/MK-2206](https://github.com/MK-2206)
- 🌐 Portfolio: [mansikharke.netlify.app](https://mansikharke.netlify.app)
- 📧 Email: [mkharke@iu.edu](mailto:mansikh.work@gmail.com)

## 📜 License

MIT License — free for personal and educational use.

---

