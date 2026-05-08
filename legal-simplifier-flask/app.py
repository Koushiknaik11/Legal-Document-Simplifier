import os
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import fitz  # PyMuPDF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load NLP Models (Global so they only load once)
# Note: You need to download the spacy model first using: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spacy model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

print("Loading Transformers models... This may take a minute on first run.")
summarizer = pipeline("text-generation", model="t5-small")
simplifier = pipeline("text-generation", model="t5-small")

print("Loading Hindi Translation Model...")
hi_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hi")
hi_model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-hi")

def translate_to_hindi(text):
    if not text:
        return text
    inputs = hi_tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
    translated_tokens = hi_model.generate(**inputs, max_length=512)
    return hi_tokenizer.decode(translated_tokens[0], skip_special_tokens=True)

# Load Legal Dictionary
with open("legal_dict.json", "r") as f:
    LEGAL_DICT = json.load(f)

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf_doc:
        for page in pdf_doc:
            text += page.get_text()
    return text

def extract_keywords(text):
    doc = nlp(text.lower())
    found_keywords = {}
    
    # Simple token matching (can be improved with phrase matching if needed)
    tokens = [token.text for token in doc]
    
    for term, meaning in LEGAL_DICT.items():
        if term in text.lower():
            found_keywords[term] = meaning
            
    return found_keywords

def chunk_text(text, max_chunk_size=512):
    # Split text into sentences using spaCy to avoid cutting off mid-sentence
    doc = nlp(text)
    chunks = []
    current_chunk = ""
    
    for sent in doc.sents:
        if len(current_chunk) + len(sent.text) < max_chunk_size:
            current_chunk += sent.text + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sent.text + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    text = ""
    
    # 1. Handle File Upload or Direct Text Input
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        elif filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
        # Clean up the file
        if os.path.exists(filepath):
            os.remove(filepath)
    else:
        text = request.form.get('text', '')
        
    target_language = request.form.get('target_language', 'en')
        
    if not text.strip():
        return jsonify({'error': 'No text provided'}), 400

    # 2. Extract Keywords
    keywords = extract_keywords(text)
    
    # Limit text size for the model to prevent memory issues and extreme delays
    if len(text) > 4000:
        text = text[:4000] + "..." # Truncate for simplicity in this demo app

    # 3. Summarize Text
    summary = ""
    try:
        # t5-small expects a "summarize: " prefix
        input_text = "summarize: " + text
        # If the text is extremely short, summarization might fail, so set min/max length carefully
        max_length = min(150, max(20, len(text.split()) // 2))
        res = summarizer(input_text, max_length=max_length, min_length=10, do_sample=False)
        summary = res[0]['summary_text']
    except Exception as e:
        print(f"Summarization error: {e}")
        summary = "Could not generate summary."

    # 4. Simplify Text
    simplified_text = ""
    try:
        # We can use chunking to simplify large texts chunk by chunk
        chunks = chunk_text(text, max_chunk_size=400)
        simplified_chunks = []
        for chunk in chunks:
            # We use t5's translation feature as a proxy for simplification, or just prompt it
            input_text = f"translate English to English: {chunk}" 
            # Note: t5-small isn't fine-tuned for pure "simplification" out of the box, 
            # but standard text2text or summarization often yields simpler sentences.
            res = simplifier(input_text, max_length=150, do_sample=True, temperature=0.7)
            simplified_chunks.append(res[0]['generated_text'])
            
        simplified_text = " ".join(simplified_chunks)
    except Exception as e:
        print(f"Simplification error: {e}")
        simplified_text = "Could not generate simplified text."

    # 5. Translate to Hindi if requested
    if target_language == 'hi':
        try:
            # Translate Summary
            if summary and summary != "Could not generate summary.":
                summary = translate_to_hindi(summary)
            
            # Translate Simplified Text (chunk it if it's too long)
            if simplified_text and simplified_text != "Could not generate simplified text.":
                simple_chunks = chunk_text(simplified_text, max_chunk_size=400)
                translated_simple = []
                for chunk in simple_chunks:
                    translated_simple.append(translate_to_hindi(chunk))
                simplified_text = " ".join(translated_simple)
                
            # Translate Keyword Meanings
            for term, meaning in keywords.items():
                keywords[term] = translate_to_hindi(meaning)
                
        except Exception as e:
            print(f"Translation error: {e}")
            # If translation fails, we append a notice but keep English text
            summary += "\n(Translation to Hindi failed)"

    return jsonify({
        'original_text': text,
        'summary': summary,
        'simplified_text': simplified_text,
        'keywords': keywords
    })

if __name__ == '__main__':
    app.run(debug=True)
