import warnings
warnings.filterwarnings('ignore')
from anonymizer import AnonymizerEngine
from entity_resolution import entityResolution
import re

engine = AnonymizerEngine()

# Input
text = open("anonymizer_text.txt", "r").read()

# Preprocess step
text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # remove gaps in numbers
text = entityResolution(text) # preprocess names

# Anonymize
anonymized_text = engine.anonymize(text)
print(anonymized_text)

# RouteLLM


# Output

