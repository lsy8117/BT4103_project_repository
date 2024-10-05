from flask import Flask, request, jsonify
from flask_cors import CORS
from anonymizer import AnonymizerEngine
from entity_resolution import enhancedEntityResolutionPipeline
import re
import io
import pymupdf
import google.generativeai as genai

engine = AnonymizerEngine()

anonymized_file_text = ""

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests (important for frontend communication)

API_KEY="AIzaSyCRu5K49RBCUPipVe02lRJgVHK1-HSvXus"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


@app.route('/mainpipeline', methods=['POST'])
def main_pipeline():
    
    #VECTOR DB
    
    query = request.form.get('query')
    query = re.sub(r'(\d)\s+(\d)', r'\1\2', query)  # remove gaps in numbers
    query = enhancedEntityResolutionPipeline(query)  # preprocess names

    # Anonymize text here
    anonymized_query = engine.anonymize(query)
    print(anonymized_query)

    # Combine the user query with the extracted anonymized PDF content
    if anonymized_file_text:
        anonymized_full_prompt = anonymized_file_text + "\n" + anonymized_query
    else:
        anonymized_full_prompt = anonymized_query
    
    # GEMINI MODEL HERE
    prompt = anonymized_full_prompt
    gemini_response = model.generate_content(prompt)
    print("Gemini response: ", gemini_response)
    if gemini_response._result.candidates and gemini_response._result.candidates[0].content.parts:
        gemini_output = gemini_response._result.candidates[0].content.parts[0].text
    else:
        gemini_output = "No text generated."

    print(f"Gemini Output: {gemini_output}")
    
    # Deanonymize text here
    deanonymized_output = engine.deanonymize(gemini_output)

    # Return the result as a JSON response
    return jsonify({'anonymized_query': anonymized_full_prompt,
                    'gemini_output': gemini_output,
                    'deanonymized_output': deanonymized_output})


@app.route('/upload', methods=['POST'])
def upload_file():
    global anonymized_file_text
    file = request.files['file'].read()

    with io.BytesIO(file) as pdf_file:
        pdf_document = pymupdf.open(stream = pdf_file, filetype="pdf")
        anonymized_file_text = ''
        for page in pdf_document:
            text = page.get_text("text")
            # text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # computationally expensive, especially for large files.
            text = enhancedEntityResolutionPipeline(text)
            anonymized_file_text += engine.anonymize(text)
    print(anonymized_file_text)
    return jsonify({'message': 'File uploaded successfully.'})


@app.route('/clear_anonymized_text', methods=['POST'])
def clear_anonymized_text():
    global anonymized_file_text
    anonymized_file_text = ""  # Clear the global variable
    return jsonify({'message': 'Anonymized file text cleared successfully.'})


if __name__ == '__main__':
    app.run(debug=True)