"""Provider contracts reserved for Phase 2 inference integration."""

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    model: str = ""


@dataclass(frozen=True)
class StructuredRequest:
    prompt: str
    schema_name: str
    model: str = ""


@dataclass(frozen=True)
class EmbeddingRequest:
    text: str
    model: str = ""


@dataclass(frozen=True)
class GenerationResult:
    text: str
    provider: str
    model: str
    request_id: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class StructuredResult:
    value: Dict[str, Any]
    provider: str
    model: str
    request_id: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class EmbeddingResult:
    vector: Any
    provider: str
    model: str
    request_id: str
    metadata: Dict[str, Any]


class InferenceProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResult:
        ...

    def structured_generate(self, request: StructuredRequest) -> StructuredResult:
        ...

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        ...
