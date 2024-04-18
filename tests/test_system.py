#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest
import numpy as np

from . import logger
from .conftest import get_scf_electronic_band_gap_template

from nomad.units import ureg
from nomad_simulations.model_system import AtomicCell, AtomsState


def test_geometry_analysis():
    atomic_cell = AtomicCell(
        length_vector_a=1.0,
        length_vector_b=1.0,
        length_vector_c=1.0,
        name='H2',
        type='original',
        positions=np.array([[0, 0.2, 0], [0, 0, 0.1]]) * ureg('angstrom'),
        atoms_state=[AtomsState(chemical_symbol='H')] * 2,
    )
    atomic_cell.normalize(None, logger)
    atomic_cell.setup_ase_analyze(atomic_cell.to_ase_atoms(logger))

    assert atomic_cell.get_bonds() == [[0.223606797749979]]  #! add approx function
