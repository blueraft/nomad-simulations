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

from structlog.stdlib import BoundLogger
from typing import Optional, List

from nomad.datamodel.data import ArchiveSection
from nomad.metainfo import Quantity, SubSection
from nomad.datamodel.metainfo.annotations import ELNAnnotation

from nomad_simulations.model_system import ModelSystem
from nomad_simulations.physical_property import PhysicalProperty
from nomad_simulations.numerical_settings import SelfConsistency
from nomad_simulations.properties import (
    FermiLevel,
    ChemicalPotential,
    CrystalFieldSplitting,
    HoppingMatrix,
    ElectronicBandGap,
    ElectronicDensityOfStates,
    ElectronicEigenvalues,
    FermiSurface,
    ElectronicBandStructure,
    AbsorptionSpectrum,
    XASSpectrum,
    Permittivity,
)


class Outputs(ArchiveSection):
    """
    Output properties of a simulation. This base class can be used for inheritance in any of the output properties
    defined in this schema.

    It contains references to the specific sections used to obtain the output properties, as well as
    information if the output `is_derived` from another output section or directly parsed from the simulation output files.
    """

    # TODO add time quantities

    normalizer_level = 2

    model_system_ref = Quantity(
        type=ModelSystem,
        description="""
        Reference to the `ModelSystem` section to which the output property references to and on
        on which the simulation is performed.
        """,
        a_eln=ELNAnnotation(component='ReferenceEditQuantity'),
    )

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # List of properties
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    fermi_levels = SubSection(sub_section=FermiLevel.m_def, repeats=True)

    chemical_potentials = SubSection(sub_section=ChemicalPotential.m_def, repeats=True)

    crystal_field_splittings = SubSection(
        sub_section=CrystalFieldSplitting.m_def, repeats=True
    )

    hopping_matrices = SubSection(sub_section=HoppingMatrix.m_def, repeats=True)

    electronic_eigenvalues = SubSection(
        sub_section=ElectronicEigenvalues.m_def, repeats=True
    )

    electronic_band_gaps = SubSection(sub_section=ElectronicBandGap.m_def, repeats=True)

    electronic_dos = SubSection(
        sub_section=ElectronicDensityOfStates.m_def, repeats=True
    )

    fermi_surfaces = SubSection(sub_section=FermiSurface.m_def, repeats=True)

    electronic_band_structures = SubSection(
        sub_section=ElectronicBandStructure.m_def, repeats=True
    )

    permittivities = SubSection(sub_section=Permittivity.m_def, repeats=True)

    absorption_spectra = SubSection(sub_section=AbsorptionSpectrum.m_def, repeats=True)

    xas_spectra = SubSection(sub_section=XASSpectrum.m_def, repeats=True)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def extract_spin_polarized_property(
        self, property_name: str
    ) -> List[PhysicalProperty]:
        """
        Extracts the spin-polarized properties if present from the property name and returns them as a list of two elements in
        which each element refers to each `spin_channel`. If the return list is empty, it means that the simulation is not
        spin-polarized (i.e., `spin_channel` is not defined).

        Args:
            property_name (str): The name of the property to be extracted.

        Returns:
            (List[PhysicalProperty]): The list of spin-polarized properties.
        """
        spin_polarized_properties = []
        properties = getattr(self, property_name)
        for prop in properties:
            if prop.spin_channel is None:
                continue
            spin_polarized_properties.append(prop)
        return spin_polarized_properties

    def set_model_system_ref(self) -> Optional[ModelSystem]:
        """
        Set the reference to the last ModelSystem if this is not set in the output. This is only
        valid if there is only one ModelSystem in the parent section.

        Returns:
            (Optional[ModelSystem]): The reference to the last ModelSystem.
        """
        if self.m_parent is not None:
            model_systems = self.m_parent.model_system
            if model_systems is not None and len(model_systems) == 1:
                return model_systems[-1]
        return None

    def normalize(self, archive, logger) -> None:
        super().normalize(archive, logger)

        # Set ref to the last ModelSystem if this is not set in the output
        if self.model_system_ref is None:
            self.model_system_ref = self.set_model_system_ref()


class SCFOutputs(Outputs):
    """
    This section contains the self-consistent (SCF) steps performed to converge an output property.

    For simplicity, we contain the SCF steps of a simulation as part of the minimal workflow defined in NOMAD,
    the `SinglePoint`, i.e., we do not split each SCF step in its own entry. Thus, each `SinglePoint`
    `Simulation` entry in NOMAD contains the final output properties and all the SCF steps.
    """

    scf_steps = SubSection(
        sub_section=Outputs.m_def,
        repeats=True,
        description="""
        Self-consistent (SCF) steps performed for converging a given output property. Note that the SCF steps belong to
        the same minimal `Simulation` workflow entry which is known as `SinglePoint`.
        """,
    )

    def get_last_scf_steps_value(
        self,
        scf_last_steps: List[Outputs],
        property_name: str,
        i_property: int,
        scf_parameters: Optional[SelfConsistency],
        logger: BoundLogger,
    ) -> Optional[list]:
        """
        Get the last two SCF values' magnitudes of a physical property and appends then in a list.

        Args:
            scf_last_steps (List[Outputs]): The list of SCF steps. This must be of length 2 in order to the method to work.
            property_name (str): The name of the physical property.
            i_property (int): The index of the physical property.
            scf_parameters (Optional[SelfConsistency]): The self-consistency parameters section stored under `ModelMethod`.
            logger (BoundLogger): The logger to log messages.

        Returns:
            (Optional[list]): The list of the last two SCF values (in magnitude) of the physical property.
        """
        # Initial check
        if len(scf_last_steps) != 2:
            logger.warning(
                '`scf_last_steps` needs to be of length 2, pointing to the last 2 SCF steps performed in the simulation.'
            )
            return []

        scf_values = []
        for step in scf_last_steps:
            try:
                scf_phys_property = getattr(step, property_name)[i_property]
                if scf_phys_property.value.u != scf_parameters.threshold_change_unit:
                    logger.error(
                        f'The units of the `scf_step.{property_name}.value` does not coincide with the units of the `self_consistency_ref.threshold_unit`.'
                    )
                    return []
            except Exception:
                return []
            scf_values.append(scf_phys_property.value.magnitude)
        return scf_values

    def resolve_is_scf_converged(
        self,
        property_name: str,
        i_property: int,
        physical_property: PhysicalProperty,
        logger: BoundLogger,
    ) -> bool:
        """
        Resolves if the physical property is converged or not after a SCF process. This is only ran
        when there are at least two `scf_steps` elements.

        Returns:
            (bool): Boolean indicating whether the physical property is converged or not after a SCF process.
        """
        # Check that there are at least 2 `scf_steps`
        if len(self.scf_steps) < 2:
            logger.warning('The SCF normalization needs at least two SCF steps.')
            return False
        scf_last_steps = self.scf_steps[-2:]

        # Check for `self_consistency_ref` section
        scf_parameters = physical_property.self_consistency_ref
        if scf_parameters is None:
            return False

        # Extract the value.magnitude of the `physical_property` to be checked if converged or not
        scf_values = self.get_last_scf_steps_value(
            scf_last_steps=scf_last_steps,
            property_name=property_name,
            i_property=i_property,
            scf_parameters=scf_parameters,
            logger=logger,
        )
        if scf_values is None or len(scf_values) != 2:
            logger.warning(
                f'The SCF normalization could not resolve the SCF values for the property `{property_name}`.'
            )
            return False

        # Compare with the `threshold_change`
        scf_diff = abs(scf_values[0] - scf_values[1])
        threshold_change = scf_parameters.threshold_change
        if scf_diff <= threshold_change:
            return True
        else:
            logger.info(
                f'The SCF process for the property `{property_name}` did not converge.'
            )
            return False

    def normalize(self, archive, logger) -> None:
        super().normalize(archive, logger)

        # Resolve the `is_scf_converged` flag for all SCF obtained properties
        for property_name in self.m_def.all_sub_sections.keys():
            # Skip the `scf_steps` and `custom_physical_property` sub-sections
            if property_name == 'scf_steps':
                continue

            # Check if the physical property with that property name is populated
            phys_properties = getattr(self, property_name)
            if phys_properties is None:
                continue
            if not isinstance(phys_properties, list):
                phys_properties = [phys_properties]

            # Loop over the physical property of the same m_def type and set `is_scf_converged`
            for i_property, phys_property in enumerate(phys_properties):
                phys_property.is_scf_converged = self.resolve_is_scf_converged(
                    property_name=property_name,
                    i_property=i_property,
                    physical_property=phys_property,
                    logger=logger,
                )
