import re
import logging
from typing import Mapping

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def case_insensitive_matching_strategy( 
    text: str, deanonymizer_mapping: Mapping[str, Mapping[str, str]]
) -> str:
    """Case insensitive matching strategy for deanonymization.

    It replaces all the anonymized entities with the original ones
        irrespective of their letter case.

    Args:
        text: Text to deanonymize.
        deanonymizer_mapping: Mapping between anonymized entities and original ones.

    Examples of matching:
        keanu reeves -> Keanu Reeves
        JOHN F. KENNEDY -> John F. Kennedy
    """

    # Iterate over all the entities (PERSON, EMAIL_ADDRESS, etc.)
    for entity_type, mappings in deanonymizer_mapping.items():
        for anonymized, original in mappings.items():
            if not anonymized:
                logger.error(f"Anonymized pattern for entity '{entity_type}' is empty. Skipping.")
                continue  # Skip empty patterns

            # Escape the anonymized string to treat it as a literal string
            escaped_anonymized = re.escape(anonymized)

            try:
                # Perform case-insensitive substitution
                text = re.sub(escaped_anonymized, original, text, flags=re.IGNORECASE)
            except re.error as e:
                logger.error(f"Regex error for pattern '{escaped_anonymized}': {e}. Skipping this pattern.")
                continue  # Skip patterns that cause regex errors

    return text