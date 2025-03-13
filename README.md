# AI SDLC - Agent POC

A proof of concept for AI agents in the software development lifecycle.

## Overview

This project demonstrates the integration of AI agents into the software development lifecycle to automate and enhance various aspects of development workflows.

## Setup

### Prerequisites

- Python 3.9+
- pip
- virtualenv (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-sdlc--agent-poc
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt  # For development
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
   > **Important**: This step is required for pre-commit hooks to work. Without it, the hooks defined in `.pre-commit-config.yaml` won't run automatically before commits.

## Development

### Code Quality

This project uses several tools to maintain code quality:

#### Ruff - Linting & Formatting

The project is configured with `.ruff.toml` that:

To run Ruff:

```bash
# Check your code with Ruff
ruff check .

# Automatically fix issues where possible
ruff check --fix .

# Format your code with Ruff
ruff format .
```

#### Pre-commit Hooks

[pre-commit](https://pre-commit.com/) is a framework for managing and maintaining pre-commit hooks.

The project includes a `.pre-commit-config.yaml` configuration that:

1. Runs Ruff for linting and formatting
2. Applies common file hygiene hooks:
   - Removes trailing whitespace
   - Ensures files end with a newline
   - Validates YAML and TOML files
   - Prevents committing large files
3. Runs pytest to ensure all tests pass before committing

To use pre-commit:

```bash
# Run pre-commit on all files
pre-commit run --all-files

# The hooks will also run automatically on git commit
```

## Testing

Run tests with pytest:

```bash
pytest
```

## License

[License details]

## Contributing

[Contributing guidelines]
