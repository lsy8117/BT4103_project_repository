from flask import Flask, request, jsonify
from flask_cors import CORS
from anonymizer import AnonymizerEngine
from entity_resolution import enhancedEntityResolutionPipeline
from vectordb import Vectordb
import re
import io
import pymupdf
import google.generativeai as genai
import os

os.environ["OPENAI_API_KEY"] = "sk-XXXXXX"
os.environ['GEMINI_API_KEY'] = "AIzaSyAikllyKYugxLfq4_JwGXkfLKyxh2D6PzA"

from routellm.controller import Controller

engine = AnonymizerEngine()

anonymized_file_text = {}

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}) # Allow cross-origin requests (important for frontend communication)

@app.route('/mainpipeline', methods=['POST'])
def main_pipeline():
    
    # Vectordb
    vectordb_api_key = "GM0ZIF4yhhRlLEdnAMh9slUJNV2hOU6JLDU7i0QOm1eocLIq-QUIzA"
    collection_name = "QnA"
    vectordb = Vectordb(vectordb_api_key)
    vectordb.set_threshold(0.8)
    # vectordb.create_collection(collection_name)

    # Query
    query = request.form.get('query')
    query = re.sub(r'(\d)\s+(\d)', r'\1\2', query)  # remove gaps in numbers
    query = enhancedEntityResolutionPipeline(query)  # preprocess names

    # Retrieve from vectordb
    response, score = vectordb.query(query, collection_name, "answer")

    # Return response from Vectordb if similar query is found
    if response != None:
        print(f"Similar query found in vectordb. Similarity score: {score}")
        print(f"Vectordb output: {response}")
        # Return the result as a JSON response
        return jsonify({
            'anonymized_query': query,
            'gemini_output': f'Similar query found in vectordb. Similarity score: {score}',
            'deanonymized_output': response, 
            'model_used': 'Vectordb'
            })
        
    # Execute main pipeline if similar query not found
    else:
        # Anonymize text here
        print("Query: ", query)
        anonymized_query = engine.anonymize(query)
        print("Anonymized_query: ", anonymized_query)
        
        # Combine the user query with the extracted anonymized PDF content
        if anonymized_file_text:
            anonymized_full_prompt = "\n".join(anonymized_file_text.values()) + "\n" + anonymized_query
        else:
            anonymized_full_prompt = anonymized_query

        prompt = anonymized_full_prompt

        client = Controller(
            routers=["bert"],
            strong_model="gemini/gemini-1.5-flash",
            weak_model="ollama_chat/seeyssimon/bt4103_gguf_finance_v2",
        )

        response = client.chat.completions.create(
            model="router-bert-0.5",
            messages=[
                {"role": "user", "content": prompt,}
            ]
        )
        model_used = response.model

        #print("response: ", response)
        response = response.choices[0].message.content
        #print("message: ", response)
        
        if response == None:
            response = "Unable to generate response"
            
        # Deanonymize text here
        deanonymized_output = engine.deanonymize(response)
        print("Deanonymized_output: ", deanonymized_output)

        # Return the result as a JSON response
        return jsonify({
            'anonymized_query': anonymized_query,
            'gemini_output': response,
            'deanonymized_output': deanonymized_output, 
            'model_used': model_used
            })


@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    for file in files:
        file_name = file.filename
        file_content = file.read()

        with io.BytesIO(file_content) as pdf_file:
            pdf_document = pymupdf.open(stream=pdf_file, filetype="pdf")
            anonymized_text = ''
            for page in pdf_document:
                text = page.get_text("text")
                # text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # computationally expensive, especially for large files.
                text = enhancedEntityResolutionPipeline(text)
                anonymized_text += engine.anonymize(text)
                
            anonymized_file_text[file_name] = anonymized_text
            print(f"Processed and anonymized: {file_name}")
    # print(anonymized_file_text)
    return jsonify({'message': f'{len(files)} file(s) uploaded and processed successfully.'})


@app.route('/clear_anonymized_text', methods=['POST'])
def clear_anonymized_text():
    file_name = request.json.get('fileName')
    if file_name in anonymized_file_text:
        del anonymized_file_text[file_name]
        # print(anonymized_file_text)
        return jsonify({'message': f'Anonymized text for {file_name} cleared successfully.'})
    else:
        return jsonify({'message': 'File not found.'})
    

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
