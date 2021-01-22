import re

import pytest

from swc_metadata import metadata


@pytest.mark.parametrize(
    'pattern,regex',
    [
        (r'abc', r'abc'),
        (r'{subject}', r'(?P<subject>[0-9]+)'),
        (r'{particle_type}', r'(?P<particle_type>local|world|wptsFeatures)'),
        (r'{chirality}', r'(?P<chirality>L|R)'),
        (r'{extension}', r'(?P<extension>nrrd|vtk|ply|particles)'),
        (r'{grooming_steps}', r'(?P<grooming_steps>[a-zA-Z]+(?:\.[a-zA-Z]+)*)'),
        (r'{subject:x}', r'(?P<subject>[0-9]+)'),
        (r'pre{subject}post', r'pre(?P<subject>[0-9]+)post'),
        (r'pre{subject:x}post', r'pre(?P<subject>[0-9]+)post'),
        (r'{undefined}', r'{undefined}'),
    ],
)
def test_pattern_as_regex(pattern, regex):
    assert metadata.pattern_as_regex(pattern) == re.compile(regex)


def test_pattern_as_regex_double_definitions():
    with pytest.raises(ValueError, match='Multiple definitions of subject'):
        metadata.pattern_as_regex(r'{subject}{subject}')


@pytest.mark.parametrize(
    'pattern,filename,expected',
    [
        (r'abc', r'abc', {}),
        (r'{subject}', r'1', {'subject': 1}),
        (r'{particle_type}', r'local', {'particle_type': 'local'}),
        (r'{chirality}', r'R', {'chirality': 'R'}),
        (r'{extension}', r'vtk', {'extension': 'vtk'}),
        (r'{grooming_steps}', r'a', {'grooming_steps': 'a'}),
        (r'{grooming_steps}', r'a.b.C.deFgHij', {'grooming_steps': 'a.b.C.deFgHij'}),
        (r'ellipsoid_{subject}_L.nrrd', 'ellipsoid_42_L.nrrd', {'subject': 42}),
        (
            r'{subject}{chirality}.{grooming_steps}_{particle_type}.{extension}',
            r'6L.isores.center.pad.com.aligned.cropped.tpSmoothDT_local.vtk',
            {
                'subject': 6,
                'chirality': 'L',
                'particle_type': 'local',
                'extension': 'vtk',
                'grooming_steps': 'isores.center.pad.com.aligned.cropped.tpSmoothDT',
            },
        ),
    ],
)
def test_extract_metadata(pattern, filename, expected):
    assert metadata.extract_metadata(pattern, filename) == expected


@pytest.mark.parametrize(
    'pattern,filename,expected',
    [
        (r'{subject}{subject}', None, 'Multiple definitions of subject'),
        (r'a', r'b', 'File b does not match pattern a'),
        (r'{subject}', r'foo', r'File foo does not match pattern {subject}'),
        (r'{particle_type}', r'extreme', r'File extreme does not match pattern {particle_type}'),
        (r'{chirality}', r'Up', r'File Up does not match pattern {chirality}'),
        (r'{extension}', r'txt', r'File txt does not match pattern {extension}'),
        (r'{grooming_steps}', r'_', r'File _ does not match pattern {grooming_steps}'),
        (r'{grooming_steps}', r'x' * 256, r'grooming_steps is more than 255 characters'),
    ],
)
def test_extract_metadata_error(pattern, filename, expected):
    with pytest.raises(ValueError, match=re.escape(expected)):
        metadata.extract_metadata(pattern, filename)


def test_generate_filename_error():
    with pytest.raises(ValueError, match='subject'):
        metadata.generate_filename('{subject}', {})


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
        (r'{subject}', r'foo', r'File foo does not match pattern {subject}'),
        (r'{subject:03}', '1', '1 does not match generated 001'),
    ],
)
def test_validate_filename_error(pattern, filename, expected):
    with pytest.raises(ValueError, match=re.escape(expected)):
        metadata.validate_filename(pattern, filename)


@pytest.mark.parametrize(
    'pattern,_metadata',
    [
        (r'abc', {}),
        (r'{subject}', {'subject': 1}),
        (r'ellipsoid_{subject}_L.nrrd', {'subject': 42}),
        (r'{subject:d}', {'subject': 2}),
        (r'{subject:03}', {'subject': 0}),
    ],
)
def test_validate_metadata(pattern, _metadata):
    metadata.validate_metadata(pattern, _metadata)


@pytest.mark.parametrize(
    'pattern,_metadata,expected',
    [
        (r'{subject}{subject}', {'subject': None}, 'Multiple definitions of subject'),
        (r'{subject}', {'subject': 'foo'}, r'File foo does not match pattern {subject}'),
    ],
)
def test_validate_metadata_error(pattern, _metadata, expected):
    with pytest.raises(ValueError, match=re.escape(expected)):
        metadata.validate_metadata(pattern, _metadata)
