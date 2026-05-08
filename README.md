# Legal Document Simplifier

A web application that takes complex legal text or documents (.txt, .pdf) and provides a simplified plain-English version, a short summary, and highlights of difficult legal words with their meanings.

## Folder Structure

```text
legal-simplifier-flask/
├── app.py                 # Main Flask application and backend logic
├── requirements.txt       # Python dependencies
├── legal_dict.json        # Dictionary of legal keywords and their meanings
├── README.md              # Project documentation
├── uploads/               # Temporary folder for uploaded files (created automatically)
├── templates/
│   └── index.html         # Frontend HTML structure
└── static/
    └── style.css          # Frontend styling
```

## Prerequisites

- Python 3.8 or higher installed.

## Installation Steps

1. **Navigate to the project directory:**
   ```bash
   cd path/to/legal-simplifier-flask
   ```

2. **Create a Virtual Environment (Optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the spaCy Language Model:**
   You must download the English language model for keyword extraction to work.
   ```bash
   python -m spacy download en_core_web_sm
   ```

## How to Run the Website

1. **Start the Flask Server:**
   ```bash
   python app.py
   ```
   *Note: On the first run, the Hugging Face Transformers models (`t5-small`) will be downloaded. This might take a minute or two depending on your internet connection.*

2. **Access the Website:**
   Open your web browser and go to:
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

3. **Usage:**
   - Upload a `.pdf` or `.txt` legal document, or directly paste text into the input box.
   - Click "Simplify & Summarize".
   - Wait for the models to process the text.
   - Read the summary, simplified text, and definitions of any detected legal terms.

## Technology Stack
- **Backend:** Python, Flask
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **NLP Models:** Hugging Face `t5-small` (Summarization/Paraphrasing), spaCy (Keyword Extraction/NER)
- **PDF Parsing:** PyMuPDF (`fitz`)
