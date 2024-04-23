import secrets
import string
from uuid import uuid4

__all__ = ["random_string", "random_hex", "random_uuid"]


def random_string(
    length: int,
    lower: bool = True,
    upper: bool = True,
    digit: bool = True,
    character_string: str = None,
) -> str:
    """Generate random string suitable for cryptographic use.

    Args:
        length (int, required):
            Length of string.
        lower (bool, optional):
            Should lowercase characters(a-z) be included. Defaults to True.
        upper (bool, optional):
            Should uppercase characters(A-Z) be included. Defaults to True.
        digit (bool, optional):
            Should digit characters(0-9) be included. Defaults to True.
        character_string (str, optional):
            String of characters from which random characters are chosen.
            If character_string is provided upper/lower/digit parameters are ignored.


    Raises:
        ValueError:
            When integer less than one or non-integer value for length is given.
            When character list to choose from is empty.

    Returns:
        str: Cryptographically-secure string of given length.
    """
    if not (length and isinstance(length, int) and length > 0):
        raise ValueError("length must be an integer greater than zero")
    chars = ""
    if lower:
        chars = chars + string.ascii_lowercase
    if upper:
        chars = chars + string.ascii_uppercase
    if digit:
        chars = chars + string.digits
    if character_string and isinstance(character_string, str):
        # if character_string is provided ignore upper/lower/digit parameters
        chars = character_string
    if not chars:
        raise ValueError("Empty character list to choose from")
    return "".join(secrets.choice(chars) for i in range(length))


_DEFAULT_ENTROPY = 64


def random_hex(nbytes: int = None) -> str:
    """Generate random hexadecimal string suitable for cryptographic use.

    Args:
        nbytes (int, optional):
            Number of bytes. Two characters generated for each byte.
            A suitable default will we used if not given.

    Returns:
        str: Cryptographically-secure hexadecimal string for given number of bytes of randomness.
    """
    if not nbytes:
        nbytes = _DEFAULT_ENTROPY  # Default
    return secrets.token_hex(nbytes=nbytes)


def random_uuid(dashes: bool = True) -> str:
    """Generate random uuid string suitable for cryptographic use.

    Args:
        dashes (bool, optional):
            should dashes be included in the generated string(uuid). Defaults to True.

    Returns:
        str: String representation of randomly generated uuid
    """
    if not dashes:
        return uuid4().hex
    return str(uuid4())
