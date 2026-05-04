from string import punctuation

import pdfplumber

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


import re

def clean_text(text):

    text = str(text).lower()
    text = re.sub(r'<[^>]+>', '', text)    # Remove HTML tags
    text = re.sub(r'&[a-z]+;', '', text) # Remove HTML entities

    text = re.sub(r'https?://\S+', '', text) # Remove URLs
    text = re.sub(r'www\.\S+', '', text) # Remove URLs
    text = re.sub(r'ftp://\S+', '', text) # Remove URLs
    text = re.sub(r'\S+\.(com|org|net|io|co|uk)\S*', '', text) # Remove domain names
    text = re.sub(r'\S+@\S+\.\S+', '', text) # Remove email addresses
    text = re.sub(r'@\w+', '', text) # Remove social media handles
    text = re.sub(r'#\w+', '', text) # Remove hashtags
    text = re.sub(r'[^\x00-\x7F]+', '', text) # Remove non-ASCII characters
    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', text) # Remove dates
    text = re.sub(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', '', text) # Remove dates
    text = re.sub(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{4}\b', '', text) # Remove dates
    text = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm)?\b', '', text) # Remove times
    text = re.sub(r'\+?[\d\s\-]{7,15}', '', text) # Remove phone numbers
    text = re.sub(r'\b\d+\.?\d*\s*(?:usd|gbp|eur|dollars?|pounds?|euros?|cents?|%)\b', '', text) # Remove currency amounts
    text = re.sub(r'[$£€¥]\s*\d+\.?\d*', '', text) # Remove currency symbols
    text = re.sub(r'\b\d+(?:\.\d+)?(?:kb|mb|gb|tb|hz|mhz|ghz|mph|kmh|kg|lb|cm|mm|km|miles?)\b', '', text) # Remove units
    text = re.sub(r'\b[A-Z]{2,}\b', '', text) # Remove uppercase words
    text = re.sub(r'\b\w*\d+\w*\b', '', text) # Remove words with numbers
    text = re.sub(r'\b[a-zA-Z]\b', '', text) # Remove single letters
    text = re.sub(r'(.)\1{2,}', r'\1', text) # Remove repeated characters
    text = re.sub(r'[^a-z\s]', '', text) # Remove punctuation and special characters
    text = text.translate(str.maketrans('', '', punctuation)) # Remove punctuation

    text = re.sub(r"\s+", " ", text)
    text = text.lower()
    return text.strip()


def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks



def process_file(file_path):
    # 1. extract
    text = extract_text_from_pdf(file_path)

    # 2. clean
    cleaned = clean_text(text)

    # 3. chunk
    chunks = chunk_text(cleaned)

    return chunks