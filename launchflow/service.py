import os
from dataclasses import dataclass
from typing import IO, Any, Dict, Generic, List, Literal, Optional, TypeVar

from launchflow.config import config
from launchflow.models.enums import ServiceProduct
from launchflow.models.flow_state import EnvironmentState
from launchflow.models.launchflow_uri import LaunchFlowURI
from launchflow.node import Node, NodeType, Outputs
from launchflow.resource import Resource
from launchflow.workflows.utils import DEFAULT_IGNORE_PATTERNS


@dataclass
class DNSRecord(Outputs):
    dns_record_value: str
    dns_record_type: Literal["A", "TXT"] = "A"


@dataclass
class DNSOutputs(Outputs):
    domain: str
    dns_records: List[DNSRecord]


@dataclass
class ServiceOutputs(Outputs):
    service_url: str
    dns_outputs: Optional[DNSOutputs]


R = TypeVar("R")


class Service(Node[ServiceOutputs], Generic[R]):
    product = ServiceProduct.UNKNOWN.value

    def __init__(
        self,
        name: str,
        *,
        build_directory: str = ".",
        build_ignore: List[str] = [],  # type: ignore
        build_diff_args: Dict[str, Any] = {},  # type: ignore
    ) -> None:
        super().__init__(name, NodeType.SERVICE)

        self._build_directory = build_directory

        self.build_ignore = list(set(build_ignore + DEFAULT_IGNORE_PATTERNS))
        self.build_diff_args = build_diff_args

        self.name = name

    @property
    def build_directory(self) -> str:
        launchflow_yaml_abspath = os.path.dirname(
            os.path.abspath(config.launchflow_yaml.config_path)
        )
        return os.path.abspath(
            os.path.join(launchflow_yaml_abspath, self._build_directory)
        )

    def resources(self) -> List[Resource]:
        raise NotImplementedError

    async def build(
        self,
        *,
        environment_state: EnvironmentState,
        launchflow_uri: LaunchFlowURI,
        deployment_id: str,
        build_log_file: IO,
        build_local: bool,
    ) -> R:
        raise NotImplementedError

    async def promote(
        self,
        *,
        from_environment_state: EnvironmentState,
        to_environment_state: EnvironmentState,
        from_launchflow_uri: LaunchFlowURI,
        to_launchflow_uri: LaunchFlowURI,
        from_deployment_id: str,
        to_deployment_id: str,
        promote_log_file: IO,
        promote_local: bool,
    ) -> R:
        raise NotImplementedError

    async def release(
        self,
        *,
        release_inputs: R,
        environment_state: EnvironmentState,
        launchflow_uri: LaunchFlowURI,
        deployment_id: str,
        release_log_file: IO,
    ) -> None:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __eq__(self, value) -> bool:
        return (
            isinstance(value, Service)
            and value.name == self.name
            and value.product == self.product
            and value.inputs() == self.inputs()
        )
