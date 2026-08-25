import hashlib
from typing import Iterable

_BITS = 64


def _token_hash(token: str) -> int:
    # A deterministic (not process-salted, unlike Python's built-in hash())
    # 64-bit hash of a single token.
    return int.from_bytes(hashlib.blake2b(token.encode('utf-8'), digest_size=8).digest(), 'big')


def simhash(text: 'str|Iterable[str]') -> int:
    """
    Locality-sensitive hash: similar text produces hashes with a small
    Hamming distance (see hamming_distance below), unlike a cryptographic
    hash where a one-character change flips roughly half the bits.
    Tokenizes on whitespace, hashes each token, and weighted-bit-votes
    across tokens into a 64-bit fingerprint.

    text may be a single string, or an iterable of strings (e.g. several
    fragments to hash as one document). Tokens are voted on per-fragment as
    the iterable is consumed, so the fragments never need to be joined into
    one big string first: since voting is a per-token sum, hashing fragments
    one at a time and hashing their concatenation give the same result, as
    long as no two fragments run together into a single token (whitespace
    ensures this at real fragment boundaries, e.g. separate lines or texts).
    """
    if isinstance(text, str):
        text = (text,)
    weights = [0] * _BITS
    any_tokens = False
    for fragment in text:
        for token in fragment.split():
            any_tokens = True
            token_hash = _token_hash(token)
            for bit in range(_BITS):
                weights[bit] += 1 if (token_hash >> bit) & 1 else -1
    if not any_tokens:
        return 0
    result = 0
    for bit in range(_BITS):
        if weights[bit] > 0:
            result |= 1 << bit
    return result


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count('1')
