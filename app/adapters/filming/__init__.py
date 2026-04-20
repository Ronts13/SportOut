from app.adapters.filming.base import FilmingProvider, HighlightRequest, HighlightResult
from app.adapters.filming.manual_upload import ManualUploadAdapter
from app.adapters.filming.pixellot import PixellotAdapter

PROVIDERS: dict[str, type[FilmingProvider]] = {
    "manual_upload": ManualUploadAdapter,
    "pixellot": PixellotAdapter,
}


def get_provider(name: str) -> FilmingProvider:
    provider_class = PROVIDERS.get(name)
    if provider_class is None:
        raise RuntimeError(
            f"Unknown filming provider: '{name}'. Available: {list(PROVIDERS)}"
        )
    return provider_class()


__all__ = [
    "FilmingProvider",
    "HighlightRequest",
    "HighlightResult",
    "ManualUploadAdapter",
    "PixellotAdapter",
    "PROVIDERS",
    "get_provider",
]
