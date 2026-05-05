from foundation_kaia.marshalling import service, endpoint
from foundation_kaia.marshalling.documenter import ServiceDocumentation
from .dto import (ControllersStatus, InstallationReport, SelfTestResult, ControllerExamples)


@service
class IControllersService:
    @endpoint(method='GET')
    def status(self) -> ControllersStatus:
        """Returns the current status of all registered controllers."""
        ...

    @endpoint(method='POST')
    def install(self, decider: str, join: bool | None = None) -> InstallationReport | None:
        """Installs a decider's Docker image and resources."""
        ...

    @endpoint(method='POST')
    def uninstall(self, decider: str, purge: bool | None = None) -> None:
        """Removes a decider's installation, optionally purging all data."""
        ...

    @endpoint(method='POST')
    def run(self, decider: str, parameter: str | None = None) -> str:
        """Starts a decider container instance and returns its instance ID."""
        ...

    @endpoint(method='POST')
    def stop(self, decider: str, instance_id: str) -> None:
        """Stops a running decider container instance."""
        ...

    @endpoint(method='POST')
    def self_test(self, decider: str) -> SelfTestResult:
        """Runs the decider's built-in self-test and returns the result."""
        ...

    @endpoint(method='GET')
    def self_test_report(self, decider: str) -> str:
        """Returns the HTML/text report from the last self-test run."""
        ...


    @endpoint(method='POST')
    def delete_self_test(self, decider: str) -> None:
        """Clears the stored self-test result for a decider."""
        ...

    @endpoint(method='GET')
    def documentation(self, name: str) -> list[ServiceDocumentation]:
        """Returns structured API documentation for a controller."""
        ...

    @endpoint(method='GET', content_type='text/html')
    def documentation_html(self, name: str) -> bytes:
        """Returns API documentation rendered as HTML."""
        ...

    @endpoint(method='GET')
    def examples(self, name: str) -> ControllerExamples:
        """Returns usage examples for a controller."""
        ...

