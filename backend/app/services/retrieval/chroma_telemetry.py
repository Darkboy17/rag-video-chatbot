from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent
from overrides import override


class NoOpTelemetryClient(ProductTelemetryClient):
    """Disable Chroma product telemetry without importing PostHog."""

    @override
    def capture(self, event: ProductTelemetryEvent) -> None:
        return None
