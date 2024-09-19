from anonymizer import AnonymizerEngine
import re
import warnings
warnings.filterwarnings('ignore')

engine = AnonymizerEngine()

text = open("anonymizer_text.txt", "r").read()

# Preprocess step
text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # remove gaps in numbers
# text = # replace names

print(engine.anonymize(text))
