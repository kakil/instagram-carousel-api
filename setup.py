from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="instagram-carousel-generator",
    version="1.0.0",
    author="Kitwana Akil",
    author_email="kit@kitwanaakil.com",
    description="API for generating Instagram carousel images with consistent styling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kakil/instagram-carousel-api",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "app": ["static/assets/*"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.109.1",
        "uvicorn>=0.23.2",
        "python-multipart>=0.0.19",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.2",
        "pydantic-settings>=2.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "httpx>=0.24.1",
            "black>=23.1.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "carousel-api=app.main:run_app",
        ],
    },
)