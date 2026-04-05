from flask import Flask, render_template, request
import PyPDF2
import os
from openai import OpenAI
import logging

app = Flask(__name__)

# Limit max upload size to 5MB
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# Logging
logging.basicConfig(level=logging.INFO)

# OpenRouter client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def predict_fake_or_real_email_content(text):
    prompt = f"""
You are an expert in identifying scam messages.

Classify the text as:
- Real/Legitimate
- Scam/Fake

Give a short answer with reason.

Text:
{text}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        logging.info("Scam detection successful.")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Scam detection failed: {e}")
        return "Error during scam detection. Please try again."

def url_detection(url):
    prompt = f"""
Classify this URL into one:
benign, phishing, malware, defacement

URL: {url}

Return only one word.
"""
    prompt = f"""
    You are an advanced AI model specializing in URL security classification. Analyze the given URL and classify it as one of the following categories:

    1. Benign**: Safe, trusted, and non-malicious websites such as google.com, wikipedia.org, amazon.com.
    2. Phishing**: Fraudulent websites designed to steal personal information. Indicators include misspelled domains (e.g., paypa1.com instead of paypal.com), unusual subdomains, and misleading content.
    3. Malware**: URLs that distribute viruses, ransomware, or malicious software. Often includes automatic downloads or redirects to infected pages.
    4. Defacement**: Hacked or defaced websites that display unauthorized content, usually altered by attackers.

    **Example URLs and Classifications:**
    - **Benign**: "https://www.microsoft.com/"
    - **Phishing**: "http://secure-login.paypa1.com/"
    - **Defacement**: "http://hacked-website.com/"
    - **Malware**: "http://free-download-software.xyz/"

    **Input URL:** {url}

    **Output Format:**  
    - Return only a string class name
    - Example output for a phishing site:  

    Analyze the URL and return the correct classification (Only name in lowercase such as benign etc.
    Note: Don't return empty or null, at any cost return the corrected class
    """
    prompt = f"""
Classify this URL strictly into ONE of these: benign, phishing, malware, defacement.
Return only one word exactly as it is in the list.
URL: {url}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        logging.info("URL detection successful.")
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        logging.error(f"URL detection failed: {e}")
        return "unknown"

# def map_classification(label):
#     label = label.lower()
#     if label == "benign":
#         return "Safe", "safe"
#     elif label == "defacement":
#         return "Warning", "warning"
#     elif label == "malware":
#         return "Danger", "danger"
#     elif label == "phishing":
#         return "Suspicious", "suspicious"
#     else:
#         return "Unknown", "unknown"

def map_classification(label):
    label = label.lower().strip()  # remove spaces
    if "benign" in label or "safe" in label:
        return "Safe", "safe"
    elif "defacement" in label or "warning" in label:
        return "Warning", "warning"
    elif "malware" in label or "danger" in label:
        return "Danger", "danger"
    elif "phishing" in label or "phishing" in label:
        return "Phishing", "phishing"
    else:
        return "Unknown", "unknown"

@app.route('/')
def index():
    return render_template("index.html")

# @app.route('/scam/', methods=['POST'])
# def detect_scam():
#     if 'file' not in request.files:
#         return render_template("index.html", message="No file uploaded. Please select a PDF or TXT file.")

#     file = request.files['file']
#     if file.filename == '':
#         return render_template("index.html", message="No file selected.")

#     extracted_text = ""

#     if file.filename.endswith('.pdf'):
#         try:
#             pdf_reader = PyPDF2.PdfReader(file)
#             text_list = [page.extract_text() for page in pdf_reader.pages if page.extract_text()]
#             extracted_text = " ".join(text_list)
#         except Exception as e:
#             logging.error(f"PDF processing error: {e}")
#             return render_template("index.html", message="Error reading PDF file. Please upload a valid PDF.")
#     elif file.filename.endswith('.txt'):
#         try:
#             extracted_text = file.read().decode("utf-8")
#         except Exception as e:
#             logging.error(f"TXT file processing error: {e}")
#             return render_template("index.html", message="Error reading TXT file. Please upload a valid text file.")
#     else:
#         return render_template("index.html", message="Invalid file type. Please upload PDF or TXT files only.")

#     if not extracted_text.strip():
#         return render_template("index.html", message="The uploaded file is empty or contains no readable text.")

#     extracted_text = extracted_text[:4000]
#     message = predict_fake_or_real_email_content(extracted_text)

#     # ✅ FIX: Only pass message, no URL/class variables here
#     return render_template("index.html", message=message)




@app.route('/predict', methods=['POST'])
def predict_url():
    url = request.form.get('url', '').strip()
    if not url:
        return render_template("index.html", message="Please enter a URL to analyze.")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    classification = url_detection(url)
    display_text, css_class = map_classification(classification)

    return render_template("index.html",
                           input_url=url,
                           predicted_class=css_class,
                           display_text=display_text)



if __name__ == '__main__':
    app.run(debug=True)