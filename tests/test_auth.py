import unittest

from nacl.signing import SigningKey

from src.utils.verify import is_fresh_timestamp, verify_key


class AuthenticationTests(unittest.TestCase):
    def test_current_timestamp_is_fresh(self):
        self.assertTrue(is_fresh_timestamp("1000", now=1000))

    def test_old_timestamp_is_rejected(self):
        self.assertFalse(is_fresh_timestamp("600", now=1000))

    def test_malformed_timestamp_is_rejected(self):
        self.assertFalse(is_fresh_timestamp("not-a-timestamp", now=1000))

    def test_malformed_signature_is_rejected(self):
        self.assertFalse(verify_key(b"{}", "invalid", "1000", "invalid"))

    def test_valid_discord_style_signature_is_accepted(self):
        signing_key = SigningKey.generate()
        timestamp = "1000"
        body = b'{"type":1}'
        signature = signing_key.sign(timestamp.encode() + body).signature.hex()
        public_key = signing_key.verify_key.encode().hex()

        self.assertTrue(verify_key(body, signature, timestamp, public_key))


if __name__ == "__main__":
    unittest.main()
