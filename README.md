# py-coders

A simple set of symmetric strongly-typed encoder/decoder classes for serializing
to and from byte-like objects.

## Usage

Coders are meant to have a simple interface:

 * `Coder.encocde(obj)` to serialize objects to a bytes-like object.
 * `Coder.decode(buf)` to deserialize objects from a byte-like object.

## Supported Coders

 * `IdentityCoder` - passes bytes through unchanged.
 * `StringCoder` - string objects, supports `ascii`, `utf8`, `utf16`, etc.
   encodings.
 * `UInt16Coder`, `UInt32Coder`, `UInt64Coder` - unsigned 16/32/64 bit integers.
   (Big-endian)
 * `JSONCoder` - JSON serializable python object
 * `PickleCoder` - Any picklable Python object.
 * `ProtobufCoder` - Google Protobuf objects. Requires `protobuf` to be
   installed.

## Compression

Any coder can be altered to compress/decompress data. Calling `Coder.compressed`
will return a coder that uses `zlib` to compress data after serialization and
decompress data before deserialization. A level (0-9) can be provided to specify
the compression level used.

## Potential Future Features

 * Stream encode/decode? May be a bit too specialized of a use case.
 * Encryption Coders.
