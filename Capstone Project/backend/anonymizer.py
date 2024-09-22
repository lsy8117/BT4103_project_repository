from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer
from langchain_experimental.data_anonymizer.deanonymizer_matching_strategies import combined_exact_fuzzy_matching_strategy

class AnonymizerEngine:
    def __init__(self):
        # Create the anonymizer with the configuration
        self.anonymizer = PresidioReversibleAnonymizer(faker_seed=42)

    def anonymize(self, text):
        # Anonymize the provided text with name standardization.
        anonymized_text = self.anonymizer.anonymize(
            text, language="en")
        return anonymized_text

    def deanonymize(self, text):
        # Deanonymize the provided text.
        deanonymized_text = self.anonymizer.deanonymize(
            text,
            deanonymizer_matching_strategy=combined_exact_fuzzy_matching_strategy,
        )
        return deanonymized_text

    def mapping(self):
        return self.anonymizer.deanonymizer_mapping
