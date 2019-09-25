# py-coders

A simple set of symmetric strongly-typed encoder/decoder classes for serializing
to and from byte-like objects. The intended use case for these is to allow for
composable encoding of raw byte arrays, operations that may be common to systems
working with low level key-value stores (memcached/Redis/LMDB/etc) or passing
binary messages in message queues (e.g. Protocol Buffers as messages in RabbitMQ).

## Usage

Coders are meant to have a simple interface:

 * `Coder.encocde(obj)` to serialize objects to a bytes-like object.
 * `Coder.decode(buf)` to deserialize objects from a byte-like object.

## Supported Base Coders

 * `IdentityCoder` - passes bytes through unchanged.
 * `StringCoder` - string objects, supports `ascii`, `utf8`, `utf16`, etc.
   encodings.
 * `IntCoder`, `UInt16Coder`, `UInt32Coder`, `UInt64Coder` - general or unsigned
   16/32/64 bit integers.  (Big-endian)
 * `JSONCoder` - JSON serializable python object
 * `PickleCoder` - Any picklable Python object.
 * `ProtobufCoder` - Google Protobuf objects. Requires `protobuf` to be
   installed.

## Chaining Coders

Coders can be chained sequentially to create sequences of encoding/decoding. For
example, to make a Coder that can encode and decode encrypted compressed JSON
blobs, the following code can be used:

```python
compressed_json_coder = ChainCoder([
                          JSONCoder(),
                          ZlibCoder(level=5),
                          EncryptedCoder(AES.new(...))
                        ])
```

This chaining is pretty common in creating composite Coders so all Coders have a
`then` function that can be used in a fluent API.

```python
compressed_json_coder = JSONCoder().then(ZlibCoder(level=5)) \
                                   .then(EncryptedCoder(AES.new(...)))
```

Three special use cases, prefixing, compression, and encryption have further
shortcuts to reduce repitition.:

```python
prefixed_int_coder = IntCoder().prefixed(prefix=b'users:')
compressed_json_coder = JSONCoder().compressed(level=5).encrypted(AES.new(...))
```

Note: what is shown here as an example may not be entirely seucre. It's meant as
an example of what can be done with the API, not what should be done. Compressing
then encrypting data may weaken security depending on the context in which it's
used.

## Sequence / Stream Processing

Coders support encoding/decoding arbitrary streams of data via `Coder.encode_all`
and `Coder.decode_all`. These operations use generator expressions, so they can
operate on arbitrarily long, possilby infinite streams of data.

```python
json_coder = JSONCoder().compressed(level=5)

# Works with normal iterables
json_blobs = json_coder.encode_all([{"name": "object_1"}, {"name": "object_2"}])

# Can run over infinite streams of inputs.
for messages in json_coder.decode_all(input_stream()):
    // Handle messages
```

Async iterators are also supported via the `Coder.encode_all_async` and
`Coder.decode_all_async` alternatives.

```python
json_coder = JSONCoder().compressed(level=5)

# Can run over infinite streams of inputs.
async for messages in json_coder.decode_all(async_input_stream()):
    // Handle messages
```

Error handling can be done without terminating the stream by providing a
`on_error` parameter.

```python
json_coder = JSONCoder().compressed(level=5)

def json_on_error(msg, exc, exc_type, traceback):
    // handle decoding errors here

# Can run over infinite streams of inputs.
async for messages in json_coder.decode_all(async_input_stream(),
                                            on_error=json_on_error):
    // Handle messages
```
