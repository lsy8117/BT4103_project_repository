from flask import Flask, request, jsonify
from flask_cors import CORS
from anonymizer import AnonymizerEngine
from entity_resolution import enhancedEntityResolutionPipeline
import re

engine = AnonymizerEngine()

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests (important for frontend communication)


@app.route('/anonymize', methods=['POST'])
def anonymize():
    data = request.json  # Get JSON data from the request
    text = data.get('text', '')
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # remove gaps in numbers
    text = enhancedEntityResolutionPipeline(text)  # preprocess names

    # Your anonymization logic here
    anonymized_text = engine.anonymize(text)

    # Return the result as a JSON response
    return jsonify({'anonymized_text': anonymized_text})


if __name__ == '__main__':
    app.run(debug=True)
