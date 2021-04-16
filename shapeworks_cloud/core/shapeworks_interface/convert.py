from pathlib import Path
from subprocess import check_call
from tempfile import TemporaryDirectory


def nrrd_to_vtp(nrrd: bytes, contour: float = 0) -> bytes:
    with TemporaryDirectory() as dir_str:
        dir = Path(dir_str)
        input_file = dir / 'input.nrrd'
        output_file = dir / 'output.vtp'
        with input_file.open('wb') as f:
            f.write(nrrd)

        check_call(
            [
                'shapeworks',
                'read-image',
                f'--name={input_file}',
                'image-to-mesh',
                '-v',
                f'{contour}',
                'write-mesh',
                f'--name={output_file}',
            ]
        )

        with output_file.open('rb') as f:
            return f.read()
