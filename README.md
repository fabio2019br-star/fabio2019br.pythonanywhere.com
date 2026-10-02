# Google News Mobile Aggregator

![MIT License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/flask-%23000.svg?logo=flask&logoColor=white)

## 📖 Description

A mobile-first news aggregator built with **Flask** that fetches and displays news from **Google News**, optimized for viewing on smartphones. The project is hosted on [PythonAnywhere](https://www.pythonanywhere.com/) and provides a clean, responsive interface for browsing headlines by category.

## ✨ Features

- 📱 Mobile-first responsive layout, optimized for small screens
- 📰 Aggregates news directly from Google News
- 🗂️ Browse headlines by category (e.g., World, Technology, Sports, Business)
- 🔗 Direct links to the original articles
- ⚡ Lightweight and fast, powered by Flask
- ☁️ Deployed on PythonAnywhere

## 🚀 Technologies Used

- [Python](https://www.python.org/) 3.8+
- [Flask](https://flask.palletsprojects.com/)
- HTML5 / CSS3 / JavaScript
- [Google News](https://news.google.com/) as the news source
- [PythonAnywhere](https://www.pythonanywhere.com/) for hosting

## 📦 Installation

### Prerequisites

- Python >= 3.8
- pip
- virtualenv (recommended)

### Step by step

```bash
# Clone the repository
git clone https://github.com/fabio2019br-star/fabio2019br.pythonanywhere.com.git

# Navigate into the project folder
cd fabio2019br.pythonanywhere.com

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application locally
python app.py
