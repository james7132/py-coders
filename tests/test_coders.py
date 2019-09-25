from coders import IdentityCoder
from coders import StringCoder
from coders import UInt16Coder, UInt32Coder, UInt64Coder
from coders import JSONCoder, PickleCoder
import unittest

PICKLE_TEST_CASES = [
    ({}, b'\x80\x03}q\x00.'),
    ([], b'\x80\x03]q\x00.'),
    ({"key": "value"},
     b'\x80\x03}q\x00X\x03\x00\x00\x00keyq\x01X\x05\x00\x00\x00valueq\x02s.')
]

COMPRESSED_TEST_CASES = [
    ({}, b'\x00{}'),
    ([], b'\x00[]'),
    ({ "key_1": "value_1", "key_2": "value_2", },
    b'\x01x\xda\xabV\xcaN\xad\x8c7T\xb2RP*K\xcc)M\x052u\x14\xc0bF\x081#\xa5Z\x00\xf7\xee\x0c\x17')
]

JSON_TEST_CASES = [
    ({}, b'{}'),
    ([], b'[]'),
    ({"key": "value"}, b'{"key": "value"}')
]


class IdentityCoderTests(unittest.TestCase):

    def test_encode(self):
        test_cases = [b'0000', b'0003', b'0020', b'0wdl', b'oqda', b'fdqz', ]
        for case in test_cases:
            with self.subTest(input=case):
                self.assertEqual(case, IdentityCoder().encode(case))

    def test_decode(self):
        test_cases = [b'0000', b'0003', b'0020', b'0wdl', b'oqda', b'fdqz', ]
        for case in test_cases:
            with self.subTest(input=case):
                self.assertEqual(case, IdentityCoder().decode(case))


class UInt16CoderTests(unittest.TestCase):

    def test_encode(self):
        test_cases = {
            0: b'\00\00',
            100: b'\x00d',
            255: b'\00\xff',
            65535: b'\xff\xff'
        }
        for val, enc in test_cases.items():
            with self.subTest(val=val, enc=enc):
                self.assertEqual(enc, UInt16Coder().encode(val))

    def test_decode(self):
        test_cases = {
            0: b'\00\00',
            100: b'\x00d',
            255: b'\00\xff',
            65535: b'\xff\xff'
        }
        for val, enc in test_cases.items():
            with self.subTest(val=val, enc=enc):
                self.assertEqual(val, UInt16Coder().decode(enc))


class UInt32CoderTests(unittest.TestCase):

    def test_encode(self):
        test_cases = {
            0: b'\00\00\00\00',
            100: b'\00\00\x00d',
            255: b'\00\00\00\xff',
            65535: b'\00\00\xff\xff',
            2 ** 32 - 1: b'\xff\xff\xff\xff'
        }
        for val, enc in test_cases.items():
            with self.subTest(val=val, enc=enc):
                self.assertEqual(enc, UInt32Coder().encode(val))

    def test_decode(self):
        test_cases = {
            0: b'\00\00\00\00',
            100: b'\00\00\x00d',
            255: b'\00\00\00\xff',
            65535: b'\00\00\xff\xff',
            2 ** 32 - 1: b'\xff\xff\xff\xff'
        }
        for val, enc in test_cases.items():
            with self.subTest(val=val, enc=enc):
                self.assertEqual(val, UInt32Coder().decode(enc))


class UInt64CoderTests(unittest.TestCase):

    def test_encode(self):
        test_cases = {
            0: b'\00\00\00\00\00\00\00\00',
            100: b'\00\00\00\00\00\00\x00d',
            255: b'\00\00\00\00\00\00\00\xff',
            65535: b'\00\00\00\00\00\00\xff\xff',
            2 ** 32 - 1: b'\00\00\00\00\xff\xff\xff\xff',
            2 ** 64 - 1: b'\xff\xff\xff\xff\xff\xff\xff\xff'
        }
        for val, enc in test_cases.items():
            with self.subTest(val=val, enc=enc):
                self.assertEqual(enc, UInt64Coder().encode(val))

    def test_decode(self):
        test_cases = {
            0: b'\00\00\00\00\00\00\00\00',
            100: b'\00\00\00\00\00\00\x00d',
            255: b'\00\00\00\00\00\00\00\xff',
            65535: b'\00\00\00\00\00\00\xff\xff',
            2 ** 32 - 1: b'\00\00\00\00\xff\xff\xff\xff',
            2 ** 64 - 1: b'\xff\xff\xff\xff\xff\xff\xff\xff'
        }
        for val, enc in test_cases.items():
            with self.subTest(val=val, enc=enc):
                self.assertEqual(val, UInt64Coder().decode(enc))


class StringCoderTests(unittest.TestCase):

    def test_encode(self):
        test_cases = [
            ("{}", b'{}'),
            ("[]", b'[]'),
            ('{"key": "value"}', b'{"key": "value"}')
        ]
        for val, enc in test_cases:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(enc, StringCoder().encode(val))

    def test_decode(self):
        test_cases = [
            ("{}", b'{}'),
            ("[]", b'[]'),
            ('{"key": "value"}', b'{"key": "value"}')
        ]
        for val, enc in test_cases:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(val, StringCoder().decode(enc))


class JSONCoderTests(unittest.TestCase):

    def test_encode(self):
        for val, enc in JSON_TEST_CASES:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(enc, JSONCoder().encode(val))

    def test_decode(self):
        for val, enc in JSON_TEST_CASES:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(val, JSONCoder().decode(enc))


class ZlibCoderTests(unittest.TestCase):

    def test_decode(self):
        coder = JSONCoder().compressed(9)
        for val, enc in COMPRESSED_TEST_CASES:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(val, coder.decode(enc))

    def test_encode(self):
        coder = JSONCoder().compressed(9)
        for val, enc in COMPRESSED_TEST_CASES:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(enc, coder.encode(val))


class PickleCoderTests(unittest.TestCase):

    def test_encode(self):
        for val, enc in PICKLE_TEST_CASES:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(enc, PickleCoder().encode(val))

    def test_decode(self):
        for val, enc in PICKLE_TEST_CASES:
            with self.subTest(val=val, enc=enc):
                self.assertEqual(val, PickleCoder().decode(enc))


if __name__ == '__main__':
    unittest.main()
