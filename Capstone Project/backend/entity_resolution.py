from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
from fuzzywuzzy import fuzz
from collections import defaultdict
import re
from transformers import logging # suppress warnings
logging.set_verbosity_error()  # suppress warnings

# Load the tokenizer and model from the same family
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-large-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-large-NER")

# Create NER pipeline
nlp = pipeline("ner", model=model, tokenizer=tokenizer)

def enhancedEntityResolutionPipeline(text):
    # Step 1: Extract and recombine names
    ner_results = nlp(text)
    
    combined_names = []
    current_entity = ""
    for token in ner_results:
        # Remove '##' and decide whether to add a space
        part = token['word'].replace('##', '')
        if token['entity'] == 'B-PER':
            if current_entity:  # If there's an ongoing entity, save it
                combined_names.append(current_entity)
            current_entity = part  # Start a new entity
        elif token['entity'] == 'I-PER' and current_entity:
            if part == '.':
                current_entity += part
            elif token['word'].startswith('##'):
                current_entity += part  # Add without space if it is part of the same word
            else:
                current_entity += ' ' + part  # Add with space if truly a separate part

    if current_entity:  # Append the last entity if any
        combined_names.append(current_entity)
        
    # Step 2: Linking similar names
    # Dictionary to hold potential links and their scores
    links = defaultdict(dict)

    # Find matches for each name excluding itself, only once per pair
    for i, name in enumerate(combined_names):
        # Loops over subsequent names to avoid comparing a name with itself and to prevent comparing pairs of names more than once.
        for other in combined_names[i+1:]:
            score = fuzz.WRatio(name, other)
            if score >= 85:
                links[name][other] = score
                links[other][name] = score  # Symmetrically link both ways to avoid later recursion

    # Determine canonical names based on name length
    canonical_names = {}
    for name, linked_names in links.items():
        # Include the original name in the comparison set
        all_names = {name} | set(linked_names.keys())
        # Determine the canonical name as the longest name
        canonical = max(all_names, key=len)
        # Assign the canonical name to all linked names and the name itself
        for n in all_names:
            canonical_names[n] = canonical
            
    # Step 3: Replace similar names with their canonical name
    # Sort the names by length in descending order to ensure that longer names (which might contain shorter names within them) are replaced first, preventing partial replacements of substrings in longer names
    sorted_names = sorted(canonical_names.items(), key=lambda x: len(x[0]), reverse=True)
    
    # List to collect all replacements
    replacements = []
    # List to keep track of the ranges in the text where replacements have been made
    replacement_ranges = []

    for original, linked in sorted_names:
        # Find all matches of the original name
        for match in re.finditer(r'\b' + re.escape(original) + r'\b', text): # Constructs a regex pattern that matches the exact original word, bracketed by word boundaries. This means original must appear as a standalone word, not as part of another word
            start, end = match.span()
            if not any(start >= r[0] and start < r[1] for r in replacement_ranges):
                replacements.append((start, end, linked))
                replacement_ranges.append((start, end))

    # Apply replacements in reverse order to avoid disrupting indices
    for start, end, linked in sorted(replacements, key=lambda x: x[0], reverse=True):
        text = text[:start] + linked + text[end:]

    return text


text1 = "Changyang, Yongsheng, and Joe are planning a trip. Changyang Yu will drive the car, Joe Chan Farn Haur will handle the route, and See Yongsheng will support any needs of the driver."

# text2 = "David Johnson and Michael D are planning a trip to Italy this summer. David has expressed interest in visiting historical sites, while Michael is looking forward to sampling the local cuisine. Additionally, David J mentioned he would love to explore the Italian countryside on a bike. Both are eager to make the most out of their travel experience, sharing updates and photos with friends."

# names = extract_names(text1)
# linked_names = link_names(names)
# new_text = replace_names(text1, linked_names)

# print("Linked Names: ", linked_names)
# print("Extracted Names: ", names)
# print("New Text : ", new_text)

print(enhancedEntityResolutionPipeline(text1))



