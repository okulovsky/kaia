import dataclasses
from ...protocol import service, endpoint, ServiceComponent
from ...documenter import ServiceDocumentation
from .html_helper import build_snippet


@service
class IDocumentationService:
    @endpoint(method='GET')
    def json(self) -> list[ServiceDocumentation]:
        """Returns structured documentation for all mounted services."""
        ...

    @endpoint(method='GET', content_type='text/html')
    def html(self) -> bytes:
        """Returns documentation for all mounted services rendered as an HTML page."""
        ...


class DocumentationService(IDocumentationService):
    def __init__(self, components: list[ServiceComponent]):
        self._docs = []
        for component in components:
            try:
                svc_doc = ServiceDocumentation.parse(type(component.service))
            except Exception:
                continue
            if component.prefix is not None:
                svc_doc = self._apply_prefix(svc_doc, component.prefix)
            self._docs.append(svc_doc)

        self._html: bytes | None = None

    def json(self) -> list[ServiceDocumentation]:
        return self._docs

    def html(self) -> bytes:
        if self._html is None:
            self._html = self._build_html()
        return self._html

    def _build_html(self) -> bytes:
        snippet = build_snippet(self._docs)
        page_css = 'body{font-family:sans-serif;max-width:960px;margin:2em auto;padding:0 1em}'
        return (
            f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<title>API Documentation</title><style>{page_css}</style></head>'
            f'<body><h1>API Documentation</h1>{snippet}</body></html>'
        ).encode('utf-8')

    @staticmethod
    def _apply_prefix(svc_doc: ServiceDocumentation, prefix: str) -> ServiceDocumentation:
        stripped = prefix.strip('/')
        old = f'/{svc_doc.name}/'
        new = f'/{stripped}/'
        corrected = {
            name: dataclasses.replace(ep, url_template=ep.url_template.replace(old, new, 1))
            for name, ep in svc_doc.endpoints.items()
        }
        return dataclasses.replace(svc_doc, name=stripped, endpoints=corrected)
