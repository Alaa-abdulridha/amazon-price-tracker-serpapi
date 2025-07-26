"""
Setup configuration for Amazon Price Tracker
Author: Alaa Abdulridha for SerpApi, LLC
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="amazon-price-tracker-serpapi",
    version="1.0.0",
    author="Alaa Abdulridha",
    author_email="alaa@serpapi.com",
    description="A powerful Amazon price tracking application powered by SerpApi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi",
    project_urls={
        "Bug Reports": "https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi/issues",
        "Source": "https://github.com/Alaa-abdulridha/amazon-price-tracker-serpapi",
        "SerpApi": "https://serpapi.com",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "amazon-tracker=main:main",
            "amazon-tracker-cli=cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "amazontracker": [
            "templates/*.html",
            "static/*",
        ],
    },
    keywords=[
        "amazon",
        "price-tracking",
        "serpapi",
        "web-scraping",
        "notifications",
        "fastapi",
        "machine-learning",
        "price-monitoring",
        "deal-alerts",
    ],
    zip_safe=False,
)
