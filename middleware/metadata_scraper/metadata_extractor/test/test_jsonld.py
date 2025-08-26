# pylint: disable-all

import unittest

from middleware.metadata_scraper.metadata_extractor.jsonld import MetadataExtractorJsonld
from middleware.metadata_scraper.metadata_extractor import MetadataParseError
from middleware.utils.test_utils import assertListofCodesEqual


class TestMetadataExtractorJsonLd(unittest.TestCase):
    def setUp(self):
        self.my_class = MetadataExtractorJsonld()
        self._url = "https://example.com"
        self._single_metadata = """
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": "John Doe"
        }
"""
        self._multiple_metadata = """
        [
            {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "John Doe"
            },
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Acme Corp"
            }
        ]
"""
        self._no_metadata = ""
        self._invalid_metadata = "### invalid ###"

    def test_single_metadata(self):
        expected_output = [
            {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "John Doe"
            }
        ]
        output = self.my_class.metadata(self._single_metadata, self._url)
        self.assertEqual(output, expected_output)

    def test_multiple_metadata(self):
        expected_output = [
            {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "John Doe"
            },
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Acme Corp"
            }
        ]
        output = self.my_class.metadata(self._multiple_metadata, self._url)
        self.assertEqual(output, expected_output)

    def test_no_metadata(self):
        with self.assertRaises(MetadataParseError):
            self.my_class.metadata(self._no_metadata, self._url)

    def test_invalid_metadata(self):
        with self.assertRaises(MetadataParseError):
            self.my_class.metadata(self._invalid_metadata, self._url)

    def test_single_raw_metadata(self):
        expected_output = [
             """
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": "John Doe"
        }
"""
        ]

        output = self.my_class.raw_metadata(self._single_metadata)
        assertListofCodesEqual(output, expected_output)

    def test_multiple_raw_metadata(self):
        expected_output = ["""
        [
            {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "John Doe"
            },
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Acme Corp"
            }
        ]
"""]
        output = self.my_class.raw_metadata(self._multiple_metadata)
        assertListofCodesEqual(output, expected_output)

    def test_no_raw_metadata(self):
        expected_output = [""]
        output = self.my_class.raw_metadata(self._no_metadata)
        assertListofCodesEqual(output, expected_output)

    def test_invalid_raw_metadata(self):
        expected_output = ["### invalid ###"]
        output = self.my_class.raw_metadata(self._invalid_metadata)
        assertListofCodesEqual(output, expected_output)

if __name__ == "__main__":
    unittest.main()