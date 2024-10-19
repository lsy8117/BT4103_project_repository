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
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import format_document
from langchain.chains.combine_documents.base import (
    DEFAULT_DOCUMENT_PROMPT,
    DEFAULT_DOCUMENT_SEPARATOR,
)
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) # get API keys from .env file
google_api_key = os.environ.get('GOOGLE_API_KEY')
vectordb_api_key = os.environ.get('VECTOR_DB_API_KEY')
from routellm.controller import Controller

engine = AnonymizerEngine()

vector_store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=google_api_key))

messages = []
file_id_tracker = {}

text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
retriever = vector_store.as_retriever()

app = Flask(__name__)
# Allow cross-origin requests (important for frontend communication)
CORS(app, resources={r"/*": {"origins": "*"}})

def generate_output(query):
    # Anonymize text here
    print("Query: ", query)
    anonymized_query = engine.anonymize(query)
    print("Anonymized_query: ", anonymized_query)
    
    docs = retriever.invoke(anonymized_query)
    print("Length: ", len(docs))
    print("Docs list: ", docs)

    anonymized_file_text = DEFAULT_DOCUMENT_SEPARATOR.join([format_document(doc, DEFAULT_DOCUMENT_PROMPT) for doc in docs])
    print("Anonymized file text: ", anonymized_file_text)

    prompt = "Context: {context} \n\n Prompt: {input}".format(context=anonymized_file_text, input=anonymized_query)

    client = Controller(
        routers=["bert"],
        strong_model="gemini/gemini-1.5-flash",
        weak_model="ollama_chat/seeyssimon/bt4103_gguf_finance_v2",
    )

    messages.append({"role": "user", "content": prompt,})

    response = client.chat.completions.create(
        model="router-bert-0.5",
        messages=messages
    )
    
    model_used = response.model

    #print("response: ", response)
    response = response.choices[0].message.content
    #print("message: ", response)
    
    if response == None:
        response = "Unable to generate response"

    messages.append({"role":"assistant", "content":response,})
    print("Messages: ", messages)
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

@app.route('/mainpipeline', methods=['POST'])
def main_pipeline():
    
    # Vectordb
    collection_name = "QnA"
    vectordb = Vectordb(vectordb_api_key)
    vectordb.set_threshold(0.8)
    # vectordb.create_collection(collection_name)

    # Query
    query = request.form.get('query')
    query = re.sub(r'(\d)\s+(\d)', r'\1\2', query)  # remove gaps in numbers
    query = enhancedEntityResolutionPipeline(query)  # preprocess names
    print("processed query: ", query)

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
        LLMresponse = generate_output(query)
        return LLMresponse

@app.route('/reprocessquery', methods=['POST'])
def reprocess_query(): # call the function when Vectordb output is irrelevant
    query = request.form.get('query')
    query = re.sub(r'(\d)\s+(\d)', r'\1\2', query)  # remove gaps in numbers
    query = enhancedEntityResolutionPipeline(query)  # preprocess names
    print("processed query: ", query)

    LLMresponse = generate_output(query)
    return LLMresponse

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    for file in files:
        file_name = file.filename
        file_content = file.read()
        page_number = 0
        lst_docs = []
        file_id_tracker[file_name] = []

        with io.BytesIO(file_content) as pdf_file:
            pdf_document = pymupdf.open(stream=pdf_file, filetype="pdf")
            anonymized_text = ''

            for page in pdf_document:
                metadata = {}
                metadata["source"] = file_name
                metadata["page"] = page_number


                text = page.get_text("text")
                # text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # computationally expensive, especially for large files.
                text = enhancedEntityResolutionPipeline(text)
                anonymized_text = engine.anonymize(text)

                page_number += 1

                doc = Document(metadata = metadata, page_content=anonymized_text)

                lst_docs.append(doc)

            splits = text_splitter.split_documents(lst_docs)

            lst_ids = vector_store.add_documents(splits)
            file_id_tracker[file_name].extend(lst_ids)

            print(f"Processed and anonymized: {file_name}")
    # print(anonymized_file_text)
    return jsonify({'message': f'{len(files)} file(s) uploaded and processed successfully.'})


@app.route('/clear_anonymized_text', methods=['POST'])
def clear_anonymized_text():
    file_name = request.json.get('fileName')
    if file_name in file_id_tracker:
        print("File name: ", file_name)
        print("File id tracker: ", file_id_tracker)
        print("File name present in file id tracker: ", file_name in file_id_tracker)
        
        vector_store.delete(file_id_tracker[file_name])
        print("Vector store: ", vector_store)

        retriever = vector_store.as_retriever()

        # print(anonymized_file_text)
        return jsonify({'message': f'Anonymized text for {file_name} cleared successfully.'})
    else:
        return jsonify({'message': 'File not found.'})

@app.route('/handle_feedback', methods=['POST'])
def handle_feedback():
    query = request.json.get("query")
    answer = request.json.get("answer")
    document = [{
        'query': query,
        'answer': answer,
    }]
    collection_name = "QnA"
    vectordb = Vectordb(vectordb_api_key)
    print("Answer", answer)
    vectordb.upload_docs(collection_name, document, "query")
    return jsonify({'message': 'Uploaded query-answer to vectorDB.'})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)