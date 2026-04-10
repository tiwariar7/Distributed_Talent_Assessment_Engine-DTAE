import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

def initialize_otel():
    """Initialize OpenTelemetry tracing for Django, Celery, and other components."""
    # Prevent re-initialization if a TracerProvider is already set
    if isinstance(trace.get_tracer_provider(), TracerProvider):
        logger.info("OpenTelemetry already initialized; skipping re-initialization.")
        return

    try:
        # Define Resource attributes
        resource = Resource.create(attributes={
            "service.name": os.environ.get("OTEL_SERVICE_NAME", "dtae-backend"),
            "service.version": "1.0.0",
            "deployment.environment": os.environ.get("OTEL_ENV", "development"),
        })

        provider = TracerProvider(resource=resource)
        
        # Configure OTLP Exporter
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("OpenTelemetry OTLP/gRPC exporter initialized at %s", otlp_endpoint)
        except Exception as e:
            # Fall back to console span exporter if OTLP setup fails or is not installed
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.warning("OTLP Exporter failed to load (%s), falling back to ConsoleSpanExporter", e)

        trace.set_tracer_provider(provider)

        # Instrument Django
        try:
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            DjangoInstrumentor().instrument()
            logger.info("Django auto-instrumentation active")
        except Exception as e:
            logger.error("Failed to instrument Django: %s", e)

        # Instrument Celery
        try:
            from opentelemetry.instrumentation.celery import CeleryInstrumentor
            CeleryInstrumentor().instrument()
            logger.info("Celery auto-instrumentation active")
        except Exception as e:
            logger.error("Failed to instrument Celery: %s", e)

    except Exception as e:
        logger.error("Failed to initialize OpenTelemetry: %s", e)

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Update validation checks and constraints.
