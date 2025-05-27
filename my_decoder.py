import gzip
import json
import zlib

"""Helper for converting the response data into json. We have to do this since 511 puts utf-8-sig encoding on the data!"""
def decode_response(response):
    # Decompress if Content-Encoding is gzip
    decompressed_data = response  # Assume no compression

    # Decode from utf-8-sig (removes BOM if present)
    decoded_text = decompressed_data.decode("utf-8-sig")

    # Parse JSON
    return json.loads(decoded_text)