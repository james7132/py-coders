import functools
import json
import pickle
import struct
import sys
import zlib
from abc import abstractmethod, ABC


class Coder(ABC):
    """An abstract base class for symmetric encoder/decoder objects."""

    @abstractmethod
    def encode(self, msg):
        """Encodes a python object into a bytes-like object"""
        pass

    @abstractmethod
    def decode(self, buf):
        """Decodes a bytes-like object into a Python object."""
        pass

    def then(self, next_coder):
        coder = ChainCoder([self, next_coder])
        if len(coder.encode_coders) == 1:
            # Optimization to reduce call overhead if the flattened chain
            # reduces to a singular coder.
            return coder.encode_coders[0]
        return coder

    def prefixed(self, prefix):
        if len(prefix) <= 0:
            return self
        return self.then(PrefixCoder(prefix=prefix))

    def compressed(self, level=-1):
        if level == 0:  # No Compression
            return self
        return self.then(ZlibCoder(level=level))

    def encrypted(self, cipher):
        return self.then(EncryptedCoder(cipher))

    def encode_all(self, msgs, on_error=None):
        """Encodes all values in a iterable of input objects.
        Calls on_error if specified on an error.
        Returns a generator of encoded values.
        """
        return Coder._apply_all(self.encode, msgs, on_error=on_error)

    def decode_all(self, bufs, on_error=None):
        """Decodes all values in a iterable of input buffers.
        Calls on_error if specified on an error.
        Returns a generator of encoded values.
        """
        return Coder._apply_all(self.decode, bufs, on_error=on_error)

    def encode_all_async(self, msgs, on_error=None):
        """Same as decode_all, but works on async iterators.
        Returns a async generate of decoded values.
        """
        return Coder._apply_all_async(self.encode, msgs, on_error=on_error)

    def decode_all_async(self, bufs, on_error=None):
        """Same as decode_all, but works on async iterators.
        Returns a async generate of decoded values.
        """
        return Coder._apply_all_async(self.decode, bufs, on_error=on_error)

    @staticmethod
    def _apply_all(func, iterable, on_error=None):
        for val in iterable:
            try:
                yield func(val)
            except Exception:
                if on_error is not None:
                    on_error(val, *sys.exc_info())
                else:
                    raise

    @staticmethod
    async def _apply_all_async(self, bufs, on_error=None):
        async for buf in bufs:
            try:
                yield self.decode(buf)
            except Exception:
                if on_error is not None:
                    on_error(buf, *sys.exc_info())
                else:
                    raise


class IdentityCoder(Coder):
    """A no-op Coder that returns the provided objects/buffers without making
    any changes.
    """

    def encode(self, msg):
        return msg

    def decode(self, buf):
        return buf


class StringCoder(Coder):
    """A Coder for string types."""

    def __init__(self, encoding="utf-8"):
        self.encoding = encoding

    def encode(self, msg):
        return msg.encode(self.encoding)

    def decode(self, buf):
        return buf.decode(self.encoding)


class ChainCoder(Coder):
    """An aggregate coder that chains multiple subcoders together.

    Example:
        ChainCoder([JSONCoder(), ZlibCoder(level=5)])

    Encoding is applied sequentially, so the output of one coder is the input
    to the next. In the above example, an JSON object is encoded by the
    JSONCoder then compressed by the ZlibCoder.
    Decoding is applied sequentially in reverse. In the above example, the
    base buffer is first decompressed by the ZlibCoder then decoded as a
    JSON object by the JSONCoder.

    A shortcut to creating chain coders can be done using Coder.then:
        JSONCoder().then(ZlibCoder(level=5))

    Note that this does not modify any existing Coders.
    """

    def __init__(self, sub_coders):
        self.encode_coders = tuple(ChainCoder._flatten_coders(sub_coders))
        self.decode_coders = tuple(reversed(self.encode_coders))

    def encode(self, msg):
        return functools.reduce(lambda m, c: c.encode(m),
                                self.encode_coders, msg)

    def decode(self, buf):
        return functools.reduce(lambda m, c: c.decode(m),
                                self.decode_coders, buf)

    @staticmethod
    def _flatten_coders(coders):
        for coder in coders:
            if isinstance(coder, ChainCoder):
                yield from ChainCoder._flatten_coders(coder.encode_coders)
            elif not isinstance(coder, IdentityCoder):
                yield coder


class IntCoder(Coder):
    """Coder for encoding integer values."""

    def __init__(self, format=">Q"):
        self.format = format

    def encode(self, msg):
        return struct.pack(self.format, msg)

    def decode(self, buf):
        return struct.unpack(self.format, buf)[0]


class UInt16Coder(IntCoder):
    """A Coder that encodes/decodes big-endian 16-bit unsigned integers."""

    def __init__(self):
        super().__init__(">H")


class UInt32Coder(IntCoder):
    """A Coder that encodes/decodes big-endian 32-bit unsigned integers."""

    def __init__(self):
        super().__init__(">L")


class UInt64Coder(IntCoder):
    """A Coder that encodes/decodes big-endian 64-bit unsigned integers."""

    def __init__(self):
        super().__init__(">Q")


class PickleCoder(Coder):
    """A Coder that encodes/decodes picklable objects."""
    def encode(self, msg):
        return pickle.dumps(msg)

    def decode(self, buf):
        return pickle.loads(buf)


class JSONCoder(StringCoder):
    """A Coder that encodes/decodes JSON objects."""

    def encode(self, msg):
        json_str = json.dumps(msg, ensure_ascii=False)
        return super(JSONCoder, self).encode(json_str)

    def decode(self, buf):
        return json.loads(super(JSONCoder, self).decode(buf))


class PrefixCoder(Coder):
    """A Coder that prepends a prefix to the input message.

    Typically not created alone, but instead by calling Coder.prefixed instead.
    This can be used to create prefixed values commonly used in key-value
    stores.
    """

    def __init__(self, prefix):
        self.prefix = prefix

    def encode(self, msg):
        return self.prefix + msg

    def decode(self, buf):
        assert buf.startswith(self.prefix)
        return buf[len(self.prefix):]


class ZlibCoder(Coder):
    """A Coder that compresses/decompresses the bytes-like objects with zlib.

    Note: this Coder does not always produce zlib compressed output. If the
    compressed output is larger than the original input, the input message is
    returned uncompressed. A header byte is prepended to specify if the message
    was compressed or not.
    """

    UNCOMPRESSED = 0
    COMPRESSED = 1

    def __init__(self, *, level=-1):
        self.level = level

    def encode(self, msg):
        compressed = zlib.compress(msg, level=self.level)
        if len(msg) < len(compressed):
            return bytes([self.UNCOMPRESSED]) + msg
        return bytes([self.COMPRESSED]) + compressed

    def decode(self, buf):
        assert len(buf) > 0
        return (zlib.decompress(buf[1:]) if buf[0] == self.COMPRESSED else
                buf[1:])


class EncryptedCoder(Coder):
    """A Coder that encrypts/decrypts buffers with a provided cipher.

    The cipher object must expose a `encrypt` and `decrypt` single argument
    methods.

    This should be compatible with PyCrypto or PyCryptodome's ciphoer objects.

    Example usage:
        from Crypto.Cipher import AES
        aes_coder = EncryptedCoder(AES.new(...))
    """

    def __init__(self, cipher):
        self.cipher = cipher

    def encode(self, msg):
        return self.cipher.encrypt(msg)

    def decode(self, buf):
        return self.cipher.decrypt(buf)


class TupleCoder(Coder):
    """Aggregate Coder that applies individual coders on specific indicies of a
    tuples.

        In: Arbitrary tuples, non-tuples will be converted into 1-tuples.
        Out: Tuple of same size encoded by the per-index encoder

    Input tuples can be smaller than the prescribed size or non-tuples. If an
    input is of smaller size, the default value will be inserted in it's place.
    """
    def __init__(self, sub_coders, default=None):
        self.coders = tuple(sub_coders)
        self.default = default

    def encode(self, msg):
        return tuple(self._to_tuple(msg, lambda c, m: c.encode(m)))

    def decode(self, msg):
        assert len(msg) == len(self.coders)
        return tuple(self._to_tuple(msg, lambda c, m: c.decode(m)))

    def _to_tuple(self, msg, func):
        msg = msg if isinstance(msg, tuple) else (msg,)
        assert len(msg) <= len(self.coders)
        for idx in range(len(self.coders)):
            if idx < len(msg):
                yield func(self.coders[idx], msg[idx])
            else:
                yield func(self.coders[idx], self.default)


class ConstCoder(Coder):
    """A Coder that returns a constant regardless of input.

    Attempting to decode with this coder will fail.
    """

    def __init__(self, const):
        self.const = const

    def encode(self, msg):
        return self.const

    def decode(self, msg):
        return None


try:
    from google.protobuf import message  # noqa: F401

    class ProtobufCoder(Coder):
        """A Coder that encodes/decodes Google ProtoBuffer objects."""

        def __init__(self, msg_type):
            self.msg_type = msg_type

        def encode(self, msg):
            assert isinstance(msg, self.msg_type)
            return msg.SerializeToString()

        def decode(self, buf):
            proto = self.msg_type()
            proto.ParseFromString(buf)
            return proto
except ImportError:
    pass
