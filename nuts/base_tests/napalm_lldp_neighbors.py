"""Query LLDP neighbors of a device."""

from typing import Dict, Callable, List, Any

import pytest
from nornir.core.task import MultiResult, Result
from nornir_napalm.plugins.tasks import napalm_get

from nuts.context import NornirNutsContext
from nuts.helpers.converters import InterfaceNameConverter
from nuts.helpers.result import AbstractHostResultExtractor, NutsResult


class LldpNeighborsExtractor(AbstractHostResultExtractor):
    def single_transform(self, single_result: MultiResult) -> Dict[str, Dict[str, Any]]:
        neighbors = self._simple_extract(single_result)["lldp_neighbors_detail"]
        return {
            peer: self._add_custom_fields(details[0])
            for peer, details in neighbors.items()
        }

    def _add_custom_fields(self, element: Dict[str, Any]) -> Dict[str, Any]:
        element = self._add_expanded_remote_port(element)
        element = self._add_remote_host(element)
        return element

    def _add_remote_host(self, element: Dict[str, Any]) -> Dict[str, Any]:
        element["remote_host"] = element["remote_system_name"]
        return element

    def _add_expanded_remote_port(self, element: Dict[str, Any]) -> Dict[str, Any]:
        element["remote_port_expanded"] = (
            InterfaceNameConverter().expand_interface_name(element["remote_port"])
        )
        return element


class LldpNeighborsContext(NornirNutsContext):
    def nuts_task(self) -> Callable[..., Result]:
        return napalm_get

    def nuts_arguments(self) -> Dict[str, List[str]]:
        return {"getters": ["lldp_neighbors_detail"]}

    def nuts_extractor(self) -> LldpNeighborsExtractor:
        return LldpNeighborsExtractor(self)


CONTEXT = LldpNeighborsContext


class TestNapalmLldpNeighbors:
    @pytest.mark.nuts("local_port,remote_host")
    def test_remote_host(
        self, single_result: NutsResult, local_port: str, remote_host: str
    ) -> None:
        lldp_neighbor_entry = single_result.result[local_port]
        assert lldp_neighbor_entry["remote_host"] == remote_host

    @pytest.mark.nuts("local_port,remote_port")
    def test_remote_port(
        self, single_result: NutsResult, local_port: str, remote_port: str
    ) -> None:
        lldp_neighbor_entry = single_result.result[local_port]
        assert (
            lldp_neighbor_entry["remote_port"] == remote_port
            or lldp_neighbor_entry["remote_port_expanded"] == remote_port
        )


class TestNapalmLldpNeighborsCount:
    @pytest.mark.nuts("neighbor_count")
    def test_neighbor_count(self, single_result, neighbor_count):
        assert neighbor_count == len(single_result.result)
