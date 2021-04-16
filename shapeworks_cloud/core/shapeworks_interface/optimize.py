from dataclasses import dataclass
from pathlib import Path
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

import numpy as np


@dataclass
class OptimizationOutput:
    local: np.ndarray
    world: np.ndarray


def generate_xml_params(
    params: Dict[str, Any],
    files: List[Path],
    output_dir: Path,
) -> str:
    params_dict = params.copy()

    for key, value in params_dict.items():
        if type(value) == bool:
            params_dict[key] = 1 if value else 0

    params_dict['attribute_scales'] = '\n'.join(['1'] * 3)
    if params_dict.get('use_normals', False):
        params_dict['attribute_scales'] += '\n' + '\n'.join(
            [f'{params_dict.get("normal_weight", 10)}'] * 3
        )
    params_dict.pop('normal_weight')

    params_dict['output_dir'] = str(output_dir)
    params_dict['inputs'] = '\n'.join(str(f) for f in files)

    elements: List[str] = []

    for key, value in params_dict.items():
        if type(value) == bool:
            value = 1 if value else 0
        elements.append(
            f"""
<{key}>
{value}
</{key}>"""
        )

    return '\n'.join(elements)


def _load_particles(path: Path, coords: str) -> np.ndarray:
    return np.asarray([np.loadtxt(f) for f in sorted(path.glob(f'*_{coords}.particles'))])


def optimize(
    files: List[Path],
    params: Dict[str, Any],
) -> OptimizationOutput:
    """Run optimization on a list of groomed shapes."""
    with TemporaryDirectory() as output_dir_str:
        output_dir = Path(output_dir_str)
        output_dir.mkdir(parents=True, exist_ok=True)
        param_xml = generate_xml_params(params, files, output_dir)
        param_xml_file = output_dir / 'params.xml'
        with param_xml_file.open('w') as f:
            f.write(param_xml)

        check_call(
            [
                'shapeworks',
                'optimize',
                '--name',
                str(param_xml_file),
            ]
        )
        return OptimizationOutput(
            local=_load_particles(output_dir, 'local'),
            world=_load_particles(output_dir, 'world'),
        )
