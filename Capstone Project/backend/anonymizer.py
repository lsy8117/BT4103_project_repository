from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer
from langchain_experimental.data_anonymizer.deanonymizer_matching_strategies import combined_exact_fuzzy_matching_strategy

analyzed_fields = ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'IBAN_CODE', 'CREDIT_CARD', 'CRYPTO', 'IP_ADDRESS', 'LOCATION',
                   #    'DATE_TIME',
                   'NRP', 'MEDICAL_LICENSE', 'URL', 'US_BANK_NUMBER', 'US_DRIVER_LICENSE', 'US_ITIN', 'US_PASSPORT', 'US_SSN', 'SG_NRIC_FIN', 'SG_UEN']

class AnonymizerEngine:
    def __init__(self):
        # Create the anonymizer with the configuration
        self.anonymizer = PresidioReversibleAnonymizer(analyzed_fields=analyzed_fields, faker_seed=42)

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
