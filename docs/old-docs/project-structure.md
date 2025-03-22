.
├── MANIFEST.in
├── README.md
├── app
│     ├── __init__.py
│     ├── api
│     │     ├── __init__.py
│     │     └── endpoints.py
│     ├── core
│     │     ├── __init__.py
│     │     ├── config.py
│     │     └── models.py
│     ├── main.py
│     ├── models
│     │     ├── __init__.py
│     │     └── carousel.py
│     ├── services
│     │     ├── __init__.py
│     │     ├── image_service
│     │     │     ├── README.md
│     │     │     ├── __init__.py
│     │     │     ├── base_image_service.py
│     │     │     ├── enhanced_image_service.py
│     │     │     ├── factory.py
│     │     │     └── standard_image_service.py
│     │     └── storage_service.py
│     ├── static
│     │     └── temp
│     │         ├── 6580222e
│     │         │     └── slide_1.png
│     │         └── a845ae05
│     │             └── slide_1.png
│     └── utils
│         ├── __init__.py
│         ├── carousel_preview.html
│         ├── html_preview_generator.py
│         ├── image_utils.py
│         └── response.json
├── app_minimal.py
├── docs
│     ├── api-flow-diagram.mermaid
│     ├── file-structure-diagram.mermaid
│     ├── implementation-plan_19March2025.md
│     ├── instagram-carousel-test-plan-updated.md
│     ├── instagram-carousel-user-guide-updated.md
│     ├── instagram-carousel-workflow.md
│     ├── n8n-workflow-implementation.md
│     ├── project-structure.txt
│     └── technical-lead-analysis (1).md
├── instagram_carousel_generator.egg-info
│     ├── PKG-INFO
│     ├── SOURCES.txt
│     ├── dependency_links.txt
│     ├── entry_points.txt
│     ├── requires.txt
│     └── top_level.txt
├── logs
│     └── temp.log
├── nginx_config.txt
├── pyproject.toml
├── requirements-dev.txt
├── requirements.txt
├── run.py
├── scripts
│     └── cleanup_temp_files.py
├── server.py
├── setup.py
├── static
│     ├── assets
│     │     └── logo.png
│     └── temp
│         └── 3df6e27e
│             └── slide_1.png
├── test.html
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_api.py
    └── test_image_service.py