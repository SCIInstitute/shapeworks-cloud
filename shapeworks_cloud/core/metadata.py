"""
Methods and constants for manipulating metadata in filenames.

For the purposes of this module, "patterns" are basically f-strings which are used to associate
bits of filenames with bits of metadata.
The only allowed variable names are the members of METADATA_FIELDS, i.e. '{subject}'.
Patterns may also include formatting information, for example '{subject:04}.txt', which will match
the filenames '0000.txt', '0001.txt', '9999.txt', etc. but will not match '1.txt'.
"""

import re
from typing import Dict

# TODO add more fields
# Fields need to be mapped from strings to however they will be used and stored
_METADATA_FIELD_TYPE_CONVERSIONS = {
    'subject': lambda subject: int(subject),
}
METADATA_FIELDS = list(_METADATA_FIELD_TYPE_CONVERSIONS.keys())


def pattern_as_regex(pattern: str):
    """Format a user specified pattern as a regular expression."""
    for field in METADATA_FIELDS:
        # This regex should match {field} and {field:expression}
        field_regex = re.compile(f'{{{ field }(?::([^{{}}]+))?}}')
        instances = field_regex.findall(pattern)
        if len(instances) == 0:
            continue
        if len(instances) > 1:
            raise ValueError(f'Multiple definitions of {field}')
        pattern = re.sub(field_regex, f'(?P<{field}>\\\\S+)', pattern)
    return re.compile(pattern)


def extract_metadata(pattern: str, filename: str):
    """Extract the metadata from a filename using the given pattern."""
    regex = pattern_as_regex(pattern)
    match = regex.fullmatch(filename)
    if match is None:
        raise ValueError(f'File {filename} does not match pattern {pattern}')
    metadata_strings = match.groupdict()
    return {
        field: _METADATA_FIELD_TYPE_CONVERSIONS[field](metadata_strings[field])
        for field in metadata_strings
    }


def generate_filename(pattern: str, metadata: Dict[str, any]):
    """Generate the filename associated with a set of metadata using the given pattern."""
    try:
        return pattern.format(**metadata)
    except KeyError as e:
        raise ValueError(e)


def validate_filename(pattern: str, filename: str):
    """Validate that a filename matches the given pattern."""
    metadata = extract_metadata(pattern, filename)
    new_filename = generate_filename(pattern, metadata)
    if filename != new_filename:
        raise ValueError(f'{filename} does not match generated {new_filename}')


def validate_metadata(pattern: str, metadata: Dict[str, any]):
    """Validate that a filename matches the given pattern."""
    filename = generate_filename(pattern, metadata)
    new_metadata = extract_metadata(pattern, filename)
    if metadata != new_metadata:
        raise ValueError(f'{metadata} does not match generated {new_metadata}')
