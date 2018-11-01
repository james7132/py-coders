import json
import struct
import pickle
import zlib
from abc import abstractmethod


class Coder(object):
    """An abstract base class for symmetric encoder/decoder objects."""
    @abstractmethod
    def encode(self, obj):
        """Encodes a python object into a bytes-like object"""
        pass

    @abstractmethod
    def decode(self, buf):
        """Decodes a bytes-like object into a Python object.

        Must return None if the provided buffer is None.
        """
        pass

    def compressed(self, level=1):
        return ZlibCoder(self, level)


class IdentityCoder(Coder):
    """A no-op Coder that returns the provided objects/buffers without making
    any changes.
    """
    def encode(self, obj): return obj

    def decode(self, buf): return None if buf is None else buf


class StringCoder(Coder):
    """A Coder for string types."""
    def __init__(self, encoding="utf8"):
        self.encoding = encoding

    def encode(self, obj):
        return obj.encode(self.encoding)

    def decode(self, buf):
        return None if buf is None else buf.decode(self.encoding)


def __create_int_coder(fmt):

    class IntCoder(Coder):

        def encode(self, obj):
            return struct.pack(fmt, obj)

        def decode(self, buf):
            return None if buf is None else struct.unpack(fmt, buf)[0]

    return IntCoder


class UInt16Coder(__create_int_coder(">H")):
    """A Coder that encodes/decodes big-endian 16-bit unsigned integers."""
    pass


class UInt32Coder(__create_int_coder(">L")):
    """A Coder that encodes/decodes big-endian 32-bit unsigned integers."""
    pass


class UInt64Coder(__create_int_coder(">Q")):
    """A Coder that encodes/decodes big-endian 64-bit unsigned integers."""
    pass


class PickleCoder(Coder):
    """A Coder that encodes/decodes picklable objects."""
    def encode(self, obj):
        return pickle.dumps(obj)

    def decode(self, buf):
        return None if buf is None else pickle.loads(buf)


class JSONCoder(StringCoder):
    """A Coder that encodes/decodes JSON objects."""
    def encode(self, obj):
        json_str = json.dumps(obj, ensure_ascii=False)
        return super(JSONCoder, self).encode(json_str)

    def decode(self, buf):
        if buf is None:
            return None
        return json.loads(super(JSONCoder, self).decode(buf))


class ZlibCoder(Coder):
    """
    A meta-Coder that compresses/decompresses the bytes-like objects with zlib
    """
    def __init__(self, subcoder, level=1):
        self.subcoder = subcoder
        self.level = level

    def encode(self, obj):
        buf = self.subcoder.encode(obj)
        return zlib.compress(buf, self.level)

    def decode(self, buf):
        if buf is None:
            return None
        decomp_buf = zlib.decompress(buf)
        return self.subcoder.decode(decomp_buf)


try:
    import protobuf                                        # noqa: F401

    class ProtobufCoder(Coder):
        """A Coder that encodes/decodes Google ProtoBuffer objects."""
        def __init__(self, proto_type):
            self.proto_type = proto_type

        def encode(self, obj):
            return obj.SerializeToString()

        def decode(self, buf):
            if buf is None:
                return None
            proto = self.proto_type()
            proto.ParseFromString(buf)
            return proto
except ImportError:
    pass
