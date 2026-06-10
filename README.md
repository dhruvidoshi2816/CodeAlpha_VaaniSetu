# VaaniSetu 🌐

**VaaniSetu** is an AI-powered multilingual translation platform that helps users communicate across languages through text, voice, images, and documents.

The platform is designed to break language barriers and provide a seamless translation experience with modern features such as voice translation, OCR-based image translation, document translation, Gen-Z slang interpretation, and translation history tracking.

---

## ✨ Features

### 🌍 Text Translation

* Translate text across 100+ languages
* Automatic language detection
* Fast and accurate translations

### 🎤 Voice Translation

* Speech-to-Text conversion
* Text-to-Speech playback
* Real-time voice interaction

### 🖼️ Image Translation

* Extract text from images using OCR
* Translate extracted content instantly

### 📄 Document Translation

* Upload and translate:

  * TXT files
  * PDF files
  * DOCX files

### 😎 Gen-Z Slang Interpreter

* Convert slang into plain English
* Understand modern internet language and abbreviations

### 📚 Translation History

* Save previous translations
* Search and review translation records

### 🎨 Modern User Experience

* Responsive design
* Dark and Light mode
* Smooth animations and transitions

---

## 🛠️ Tech Stack

### Frontend

* React.js
* Tailwind CSS
* Framer Motion
* Axios

### Backend

* Flask
* SQLite
* Tesseract OCR
* Translation APIs

---

## 📋 Requirements

* Python 3.11+
* Node.js 18+
* npm
* Tesseract OCR (for image translation)

---

## 🚀 Setup

### Backend

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

copy .env.example .env

python app.py
```

Backend runs at:

```text
http://localhost:5000
```

---

### Frontend

```bash
cd frontend

npm install

copy .env.example .env

npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## ⚙️ Environment Variables

### Backend (.env)

```env
OPENAI_API_KEY=your_api_key
SECRET_KEY=your_secret_key
TESSERACT_CMD=path_to_tesseract
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:5000/api
```

---

## 📂 Project Structure

```text
VaaniSetu
│
├── backend
│   ├── routes
│   ├── services
│   ├── models
│   ├── tessdata
│   ├── requirements.txt
│   └── app.py
│
├── frontend
│   ├── src
│   │   ├── pages
│   │   ├── components
│   │   ├── api
│   │   └── hooks
│   │
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── .gitignore
```

---

## 🔌 API Endpoints

| Method | Endpoint                   | Description             |
| ------ | -------------------------- | ----------------------- |
| GET    | `/api/health`              | Health Check            |
| POST   | `/api/translate/translate` | Text Translation        |
| POST   | `/api/slang/translate`     | Slang Translation       |
| GET    | `/api/slang/glossary`      | Slang Dictionary        |
| POST   | `/api/ocr/extract`         | Extract Text From Image |
| POST   | `/api/ocr/translate-image` | OCR + Translation       |
| POST   | `/api/document/translate`  | Document Translation    |
| GET    | `/api/history`             | Translation History     |

---

## 🎯 Project Objective

The goal of VaaniSetu is to provide a unified multilingual communication platform that supports multiple translation methods while maintaining ease of use, accessibility, and modern user experience.

By combining text, voice, image, and document translation into a single application, VaaniSetu helps users communicate effectively regardless of language barriers.

---

## 📸 Screenshots

Add screenshots of:

* Home Page
* Text Translation
* Voice Translation
* OCR Translation
* Document Translation
* History Dashboard

---

