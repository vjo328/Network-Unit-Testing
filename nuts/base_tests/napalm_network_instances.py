"""Query network instances of a device."""

import copy
import re
from typing import Dict, List, Callable, Any

import pytest
from nornir.core.task import MultiResult, Result
from nornir_napalm.plugins.tasks import napalm_get

from nuts.helpers.result import AbstractHostResultExtractor, NutsResult
from nuts.context import NornirNutsContext


class NetworkInstancesExtractor(AbstractHostResultExtractor):
    def single_transform(self, single_result: MultiResult) -> Dict[str, Dict[str, Any]]:
        network_instances = self._simple_extract(single_result)["network_instances"]
        return {
            instance: self._transform_single_network_instance(details)
            for instance, details in network_instances.items()
        }

    def _transform_single_network_instance(
        self, network_instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "route_distinguisher": network_instance["state"]["route_distinguisher"],
            "interfaces": list(network_instance["interfaces"]["interface"]),
        }


class NetworkInstancesContext(NornirNutsContext):
    def nuts_task(self) -> Callable[..., Result]:
        return napalm_get

    def nuts_arguments(self) -> Dict[str, List[str]]:
        return {"getters": ["network_instances"]}

    def nuts_extractor(self) -> NetworkInstancesExtractor:
        return NetworkInstancesExtractor(self)


CONTEXT = NetworkInstancesContext


class TestNapalmNetworkInstances:
    @pytest.mark.nuts("network_instance")
    def test_network_instance_exists(self, single_result, network_instance):
        assert network_instance in single_result.result

    @pytest.mark.nuts("network_instance,interfaces")
    def test_network_instance_contains_interfaces(
        self, single_result: NutsResult, network_instance: str, interfaces: List[str]
    ) -> None:
        result = copy.deepcopy(single_result.result[network_instance]["interfaces"])
        patterns = len(interfaces)
        matches = 0
        for interface in interfaces:
            pattern = re.compile(interface)
            for i in result:
                if pattern.match(i):
                    single_result.result[network_instance]["interfaces"].remove(i)
            if len(result) != len(single_result.result[network_instance]["interfaces"]):
                result = copy.deepcopy(
                    single_result.result[network_instance]["interfaces"]
                )
                matches += 1
        assert patterns == matches
        assert result == []

    @pytest.mark.nuts("network_instance,route_distinguisher")
    def test_route_distinguisher(
        self, single_result: NutsResult, network_instance: str, route_distinguisher: str
    ) -> None:
        assert (
            single_result.result[network_instance]["route_distinguisher"]
            == route_distinguisher
        )
