"""
Setup script for the Instagram Carousel Generator package.

This module handles the installation and package configuration of the
Instagram Carousel Generator, defining dependencies, metadata, and
entry points for the application.
"""
from setuptools import find_packages, setup

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
    package_data={"app": ["static/assets/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.23.2",
        "python-multipart==0.0.9",  # Using older version without vulnerability
        "Pillow>=10.3.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.2",
        "pydantic-settings>=2.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.2.0",
            "httpx>=0.24.1",
            "black>=24.3.0",  # Updated to fix CVE-2024-21503
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
