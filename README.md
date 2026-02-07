# 🏗️ SiteMate Pro: The Enterprise Construction OS

> **"From Blueprint to Bank Alert – The Operating System for Modern African Construction."**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sitemate-construction-agent-r9kobvwbkzdomykfe9cmgy.streamlit.app) 
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Competition](https://img.shields.io/badge/Built%20For-Algolia%20Agent%20Studio%20Challenge-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## 📖 Overview
**[🔴 LIVE DEMO: Click here to try SiteMate Pro](https://sitemate-construction-agent-r9kobvwbkzdomykfe9cmgy.streamlit.app)**

**SiteMate Pro** is an AI-powered "Enterprise Operating System" designed to solve the fragmentation, opacity, and inefficiency in the Nigerian construction industry. It unifies project planning, procurement, site operations, and financial reporting into a single, cohesive platform.

Built specifically for the **Algolia Agent Studio Challenge**, SiteMate Pro leverages **Algolia's** powerful search and sync capabilities to connect engineers with real-time material prices and suppliers instantly.

---

## 🎥 Demo Walkthrough

[![Watch the Video](https://img.youtube.com/vi/PLACEHOLDER_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=PLACEHOLDER_VIDEO_ID)

*(Click the image above to watch the project demo)*

---

## 🚀 Key Features

### 1. 📐 AI Engineering Architect
* **Voice-to-BOQ:** Speak your project idea (e.g., *"I want to build a 4-bedroom duplex in Lekki"*), and the AI generates a professional **Bill of Quantities (BOQ)** instantly.
* **Location-Aware Estimation:** Adjusts material costs and structural recommendations based on location (e.g., "Swampy" soil in Lekki vs. "Dry" soil in Ibadan).
* **Export:** Download professional PDF reports for banks or clients.

### 2. 🛒 Procurement Marketplace (Powered by Algolia)
* **Live Bidding System:** Post material needs and receive bids from suppliers.
* **Smart Search:** Instantly find suppliers and materials using Algolia's index.
* **AI Price Judgment:** The system flags bids as "Fair," "High," or "Suspiciously Low" based on real-time market data.

### 3. 🚧 Site Operations Manager
* **Digital DSR (Daily Site Report):** Log labor, weather, and progress daily.
* **Inventory Control:** Track stock levels (Cement, Sand, Granite) with visual charts.
* **Expense Ledger:** Record every Naira spent and generate financial audits automatically.

### 4. 🚚 Supplier Portal
* **Vendor Dashboard:** Suppliers can view open tenders, submit bids, and track their win/loss history.
* **Seamless Registration:** Easy onboarding for new local suppliers.

---

### 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend & UI** | [Streamlit](https://streamlit.io/) |
| **Search & Data Sync** | [Algolia](https://www.algolia.com/) (Agent Studio) |
| **LLM & Reasoning** | Google Gemini (Generative AI) |
| **Speech Processing** | Groq (Whisper-large-v3 for ultra-fast transcription) |
| **Data Visualization** | Altair & Matplotlib |
| **Reporting** | FPDF (Automated PDF generation) |

---

### 📸 Screenshots

| **Command Center** | **Procurement Marketplace** |
|:---:|:---:|
| ![Command Center](assets/command_center.png) | ![Marketplace](assets/marketplace.png) |
| *Real-time project dashboard* | *Live bidding and supplier analysis* |

> *Note: Application screenshots reside in the `assets/` folder.*

---

## ⚡ Installation & Setup

Want to run this locally? Follow these steps:

### 1. Clone the Repository
```bash
git clone [https://github.com/AdMub/Sitemate-Construction-Agent.git](https://github.com/AdMub/Sitemate-Construction-Agent.git)
cd Sitemate-Construction-Agent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r sitemate_app/requirements.txt
```

### **4. Set Up Environment Variables Create a .env file in the root directory and add your API keys:**
```Ini, TOML
GOOGLE_API_KEY = "your_google_key"
ALGOLIA_APP_ID = "your_algolia_id"
ALGOLIA_API_KEY = "your_algolia_key"
GROQ_API_KEY = "your_groq_key"
```

### **5. Run the App**
```bash
streamlit run sitemate_app/app.py
```

### **👨‍💻 Author**
**Mubarak Adisa**
  
- 🎓 Civil Engineering + Computer Science (Data Science & AI Focus)  
- 🔗 GitHub: [AdMub](https://github.com/AdMub)  
- 💼 LinkedIn: [Mubarak Adisa](https://www.linkedin.com/in/mubarak-adisa-334a441b6/)  


### **📄 License**
Distributed under the MIT License. See `LICENSE` for more information.

### **🌟 Acknowledgements**
- Built for the Algolia Agent Studio Challenge 2026.
- Powered by Algolia, Groq, Google Gemini, and Streamlit.