"""Setup configuration for Azure Reporting Tool."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="azure-reporting-tool",
    version="1.0.0",
    author="tsimiz",
    description="Tool to easily create a report and analysis of Azure environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tsimiz/azureReportingTool",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Documentation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "azure-identity>=1.15.0",
        "azure-mgmt-resource>=23.0.0",
        "azure-mgmt-compute>=30.5.0",
        "azure-mgmt-network>=25.2.0",
        "azure-mgmt-storage>=21.1.0",
        "azure-mgmt-monitor>=6.0.0",
        "azure-mgmt-security>=6.0.0",
        "openai>=1.12.0",
        "python-pptx>=0.6.23",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
        "pandas>=2.2.0",
    ],
    entry_points={
        "console_scripts": [
            "azure-reporter=azure_reporter.main:main",
        ],
    },
)
