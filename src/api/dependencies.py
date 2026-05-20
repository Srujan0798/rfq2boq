"""API dependencies and container."""

from dataclasses import dataclass

from src.domain.boq_assembler import BOQAssembler
from src.ontology.loader import OntologyLoader


@dataclass
class PipelineContainer:
    assembler: BOQAssembler | None = None
    ontology: OntologyLoader | None = None


_container: PipelineContainer | None = None


def get_pipeline_container() -> PipelineContainer:
    global _container
    if _container is None:
        _container = PipelineContainer(
            assembler=BOQAssembler(),
            ontology=OntologyLoader(),
        )
    return _container


async def get_current_tenant(request):
    from src.auth.tenant import get_current_tenant as _get_current_tenant
    return await _get_current_tenant(request)


async def get_current_user(request):
    from src.auth.security import verify_jwt
    return await verify_jwt(request)
