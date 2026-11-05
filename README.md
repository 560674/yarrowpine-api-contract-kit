# Yarrowpine API Contract Kit

*Templates and a checker for OpenAPI™ documents — free edition*

OpenAPI™ is a trademark of The Linux Foundation. Python® is a registered trademark of the Python Software Foundation. Independent product, not affiliated with, endorsed by, or sponsored by The Linux Foundation, the OpenAPI Initiative or the Python Software Foundation.

```bash
pip install -e ".[dev]"
ypapi list
ypapi init crud-resource -o openapi.yaml --title "YourBrand"
ypapi lint openapi.yaml
```

**Free edition:** 3 templates (`minimal`, `crud-resource`, `problem-details-errors`) and 6 error rules
(version, info, paths, unique operationIds, $ref resolution, path parameters).

Yarrowpine API Contract Kit Pro adds 5 more templates (auth, cursor pagination, webhooks, file upload, a full store example),
9 more rules (responses, security schemes, naming, summaries, error responses, tags, unused components, HTTPS servers,
examples), a style guide, review checklist, docs templates and more tests.

All example APIs are fictional and use example.com. Runtime dependency: PyYAML (MIT), installed from PyPI.

MIT License. Copyright (c) 2026 Yarrowpine Studio.
