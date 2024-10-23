from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
from rapidfuzz import fuzz
from collections import defaultdict
import re
from transformers import logging # suppress warnings
logging.set_verbosity_error()  # suppress warnings
import string

# Load the tokenizer and model from the same family
tokenizer = AutoTokenizer.from_pretrained(
    "dslim/bert-large-NER", clean_up_tokenization_spaces=True)
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-large-NER")

# Create NER pipeline
nlp = pipeline("ner", model=model, tokenizer=tokenizer)

# Track the names that appear so far for the current conversation
current_unique_names = set()
# Track the canonical names that anonymizer uses to anonymize names
current_canonical_names = set()

def enhancedEntityResolutionPipeline(text):
    def is_last_char_punctuation(text):
        if text and text[-1] in string.punctuation:
            return True
        return False

    # Check if the text ends with a period, because if the name appears as the last word of the sentence but without a period, the NER won't recognize it as a name.
    if not is_last_char_punctuation(text):
        text += '.'
        
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
        
    # Update global unique names and prepare for linkage
    new_names_set = set(combined_names)
    current_unique_names.update(new_names_set)
    print('Global Unique Names: ', current_unique_names)

    # Step 2: Linking similar names and selecting the canonical name for each group of similar names
    # Dictionary to hold potential links
    links = defaultdict(set)
    # Initialize links dictionary with new names to include single names in current text
    for name in new_names_set:
        links[name] = set()

    # Find matches for each name excluding itself, only once per pair
    for i, name in enumerate(current_unique_names):
        # Loops over subsequent names to avoid comparing a name with itself and to prevent comparing pairs of names more than once.
        for other in list(current_unique_names)[i+1:]:
            score = fuzz.WRatio(name, other)
            if score >= 70:
                links[name].add(other)
                links[other].add(name) # Symmetrically link both ways to avoid later recursion

    print('Current Linking Names ', links)
    # Determine canonical names based on name length
    canonical_names = {}
    for name, linked_names in links.items():
        if linked_names:
            # Include the original name in the comparison set
            all_names = {name} | linked_names
            # Prioritize existing canonical names if present
            potential_canonical_candidate = (current_canonical_names & all_names)
            if potential_canonical_candidate:
                canonical = potential_canonical_candidate.pop()
            else:
                # Determine the canonical name as the longest name
                canonical = max(all_names, key=len)
                # Add the canonical name for this group to the global canonical name list
                current_canonical_names.add(canonical)
            
            # Assign the canonical name to all linked names and the name itself
            for n in all_names:
                canonical_names[n] = canonical
        else:
            # Handle names without linking names directly
            current_canonical_names.add(name)
    
    print('Current Canonical Name Dic: ', canonical_names)
    print('Global Canonical Names: ', current_canonical_names)
    # Step 3: Replace similar names with their canonical name
    # Sort the names by length in descending order to ensure that longer names (which might contain shorter names within them) are replaced first, preventing partial replacements of substrings in longer names
    sorted_names = sorted(canonical_names.items(), key=lambda x: len(x[0]), reverse=True)
    print("Sorted Names: ", sorted_names)
    
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


# text1 = "Changyang, Yongsheng, and Joe are planning a trip. Changyang Yu will drive the car, Joe Chan Farn Haur will handle the route, and See Yongsheng will support any needs of the driver."

# text2 = "David Johnson and Michael D are planning a trip to Italy this summer. David has expressed interest in visiting historical sites, while Michael is looking forward to sampling the local cuisine. Additionally, David J mentioned he would love to explore the Italian countryside on a bike. Both are eager to make the most out of their travel experience, sharing updates and photos with friends."

# names = extract_names(text1)
# linked_names = link_names(names)
# new_text = replace_names(text1, linked_names)

# print("Linked Names: ", linked_names)
# print("Extracted Names: ", names)
# print("New Text : ", new_text)

# print(enhancedEntityResolutionPipeline(text1))



