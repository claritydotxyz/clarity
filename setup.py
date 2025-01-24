from setuptools import setup, find_packages

setup(
    name="clarity",
    version="0.1.0",
    description="AI Resource Compass - Personal efficiency dashboard",
    author="Clarity Team",
    author_email="team@claritys.xyz",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.100.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "python-dotenv>=1.0.0",
        "uvicorn[standard]>=0.23.0",
        "psycopg2-binary>=2.9.0",
        "redis>=5.0.0",
        "celery>=5.3.0",
        "torch>=2.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "plaid-python>=15.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "mypy>=1.4.0",
            "pylint>=2.17.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "clarity=clarity.cli:main",
        ],
    },
)
