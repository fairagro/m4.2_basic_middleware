import unittest

from metadata_scraper.metadata_extractor.metadata_extractor_embedded_jsonld import MetadataExtractorEmbeddedJsonld
from metadata_scraper.metadata_extractor import MetadataParseError
from utils import assertListofCodesEqual


class TestMetadataExtractorJsonLd(unittest.TestCase):
    def setUp(self):
        self.my_class = MetadataExtractorEmbeddedJsonld()
        self._url = "https://example.com"
        self._single_metadata = """
        <html>
            <head>
                <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "Person",
                        "name": "John Doe"
                    }
                </script>
            </head>
            <body>
                <h1>Hello World</h1>
            </body>
        </html>
"""
        self._multiple_metadata = """
        <html>
            <head>
                <script type="application/ld+json">
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
                </script>
            </head>
            <body>
                <h1>Hello World</h1>
            </body>
        </html>
"""
        self._no_metadata = """
        <html>
            <head>
                <script type="application/ld+json">
                </script>
            </head>
            <body>
                <h1>Hello World</h1>
            </body>
        </html>
"""
        self._invalid_metadata = """
        <html>
            <head>
                <script type="application/ld+json">
                    ### invalid ###
                </script>
            </head>
            <body>
                <h1>Hello World</h1>
            </body>
        </html>
"""
        self._invalid_html = """
        <html>
            <### invalid ###>
                <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "Person",
                        "name": "John Doe"
                    }
                </script>
            </head>
            <### invalid ###>
                <h1>Hello World</h1>
            </body>
        </html>
"""

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

    def test_invalid_html(self):
        expected_output = [
            {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "John Doe"
            }
        ]
        output = self.my_class.metadata(self._single_metadata, self._url)
        self.assertEqual(output, expected_output)

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
"""
        ]
        output = self.my_class.raw_metadata(self._multiple_metadata)
        assertListofCodesEqual(output, expected_output)

    def test_no_raw_metadata(self):
        expected_output = [""]
        output = self.my_class.raw_metadata(self._no_metadata)
        assertListofCodesEqual(output, expected_output)

    def test_invalid_html_raw(self):
        expected_output = [
             """
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": "John Doe"
        }
"""
        ]
        output = self.my_class.raw_metadata(self._invalid_html)
        assertListofCodesEqual(output, expected_output)

    def test_invalid_raw_metadata(self):
        expected_output = ["### invalid ###"]
        output = self.my_class.raw_metadata(self._invalid_html)
        assertListofCodesEqual(output, expected_output)

if __name__ == "__main__":
    unittest.main()