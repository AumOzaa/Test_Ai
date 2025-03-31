from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import PyPDF2
import io
import os
import re
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
app.config['UPLOAD_FOLDER'] = 'uploads'

# Hardcoded API key - replace with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyBuDeOd_at1IcRPc-rRVoKMwHeXA6Tj2wc"

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_text_from_pdf(pdf_file):
    """Extract text content from PDF file"""
    text = ""
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text() or ""  # Handle None from extract_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_test_cases(text):
    """Parse the test cases from the generated text into structured format"""
    test_cases = []
    
    # Updated pattern to be more flexible with whitespace and optional fields
    pattern = r"Test Case ID:\s*(.*?)\s*\n.*?Requirement Reference:\s*(.*?)\s*\n.*?Description:\s*(.*?)\s*\n.*?Preconditions:\s*(.*?)\s*\n.*?Test Steps:\s*(.*?)\s*\n.*?Expected Results:\s*(.*?)(?=\n\s*Test Case ID:|\s*$)"
    
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for i, match in enumerate(matches):
        if match:
            test_case = {
                'id': match.group(1).strip(),
                'requirement': match.group(2).strip(),
                'description': match.group(3).strip(),
                'preconditions': match.group(4).strip(),
                'steps': match.group(5).strip(),
                'expected': match.group(6).strip(),
                'type': determine_test_case_type(match.group(3).strip())
            }
            test_cases.append(test_case)
    
    if not test_cases:
        print("Warning: No test cases parsed from the response")
    
    return test_cases

def determine_test_case_type(description):
    """Determine the test case type based on description"""
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['invalid', 'negative', 'error', 'fail']):
        return 'Negative'
    elif any(word in description_lower for word in ['boundary', 'edge', 'limit', 'maximum', 'minimum']):
        return 'Boundary'
    else:
        return 'Positive'

def generate_test_cases(srs_text):
    """Generate test cases from SRS document using Gemini API"""
    if not srs_text:
        return None, "No text extracted from SRS document"
    
    try:
        # Configure Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        # Updated prompt for stricter formatting
        prompt = f"""Analyze the following SRS document and generate test cases in this exact format:
        Test Case ID: TCXXX
        Requirement Reference: REQXXX
        Description: [description]
        Preconditions: [preconditions]
        Test Steps: [steps]
        Expected Results: [results]
        
        Include positive, negative, and boundary cases for each functional requirement.
        Also include test cases for non-functional requirements (performance, security, etc.).
        Separate each test case with a blank line.
        
        Here is the SRS document:
        {srs_text}
        """
        
        response = model.generate_content(prompt)
        print("Gemini API Response:", response.text)  # Debug output
        
        # Parse the test cases from the response
        test_cases = parse_test_cases(response.text)
        
        if not test_cases:
            return [], "No test cases could be parsed from the document"
        
        return test_cases, None
    except Exception as e:
        return None, f"Error generating test cases: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'pdf' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['pdf']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        # Save the file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        with open(filepath, 'rb') as pdf_file:
            extracted_text = extract_text_from_pdf(pdf_file)
        
        # Remove the temporary file
        os.remove(filepath)
        
        if not extracted_text:
            return jsonify({"error": "Failed to extract text from PDF"}), 400
        
        # Generate test cases
        test_cases, error = generate_test_cases(extracted_text)
        
        if error:
            return jsonify({"test_cases": [], "warning": error}), 200  # Return empty list with warning
        
        return jsonify({"test_cases": test_cases}), 200
    
    return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

@app.route('/download/csv', methods=['POST'])
def download_csv():
    if not request.json or 'test_cases' not in request.json:
        return jsonify({"error": "No test cases provided"}), 400
    
    test_cases = request.json['test_cases']
    
    # Create a CSV in memory
    output = io.StringIO()
    fieldnames = ['id', 'requirement', 'description', 'preconditions', 'steps', 'expected', 'type']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(test_cases)
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=test_cases.csv'
    }

if __name__ == '__main__':
    app.run(debug=True)