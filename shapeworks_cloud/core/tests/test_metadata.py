import re

import pytest

from shapeworks_cloud.core import metadata


@pytest.mark.parametrize(
    'pattern,regex',
    [
        (r'abc', r'abc'),
        (r'{subject}', r'(?P<subject>\S+)'),
        (r'{subject:x}', r'(?P<subject>\S+)'),
        (r'pre{subject}post', r'pre(?P<subject>\S+)post'),
        (r'pre{subject:x}post', r'pre(?P<subject>\S+)post'),
        (r'{undefined}', r'{undefined}'),
    ],
)
def test_pattern_as_regex(pattern, regex):
    assert metadata.pattern_as_regex(pattern) == re.compile(regex)


def test_pattern_as_regex_double_definitions():
    try:
        metadata.pattern_as_regex(r'{subject}{subject}')
        raise Exception('Expected an exception')
    except ValueError as e:
        assert e.args == ('Multiple definitions of subject',)


@pytest.mark.parametrize(
    'pattern,filename,expected',
    [
        (r'abc', r'abc', {}),
        (r'{subject}', r'1', {'subject': 1}),
        (r'ellipsoid_{subject}_L.nrrd', 'ellipsoid_42_L.nrrd', {'subject': 42}),
    ],
)
def test_extract_metadata(pattern, filename, expected):
    assert metadata.extract_metadata(pattern, filename) == expected


@pytest.mark.parametrize(
    'pattern,filename,expected',
    [
        (r'{subject}{subject}', None, 'Multiple definitions of subject'),
        (r'a', r'b', 'File b does not match pattern a'),
        (r'{subject}', r'foo', "invalid literal for int() with base 10: 'foo'"),
    ],
)
def test_extract_metadata_error(pattern, filename, expected):
    try:
        metadata.extract_metadata(pattern, filename)
        raise Exception('Expected an exception')
    except ValueError as e:
        assert e.args == (expected,)


@pytest.mark.parametrize(
    'pattern,filename',
    [
        (r'abc', r'abc'),
        (r'{subject}', r'1'),
        (r'ellipsoid_{subject}_L.nrrd', 'ellipsoid_42_L.nrrd'),
        (r'{subject:d}', r'2'),
        (r'{subject:03}', r'000'),
    ],
)
def test_validate_filename(pattern, filename):
    metadata.validate_filename(pattern, filename)


@pytest.mark.parametrize(
    'pattern,filename,expected',
    [
        (r'{subject}{subject}', None, 'Multiple definitions of subject'),
        (r'a', r'b', 'File b does not match pattern a'),
        (r'{subject}', r'foo', "invalid literal for int() with base 10: 'foo'"),
        (r'{subject:03}', '1', '1 does not match generated 001'),
    ],
)
def test_validate_filename_error(pattern, filename, expected):
    try:
        metadata.validate_filename(pattern, filename)
        raise Exception('Expected an exception')
    except ValueError as e:
        assert e.args == (expected,)
