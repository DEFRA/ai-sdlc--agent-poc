# Scripts

This directory contains utility scripts for development, documentation, and maintenance tasks.

## Available Scripts

### Graph Diagram Generator (`generate_graph_diagrams.py`)

Automatically generates Mermaid diagrams for LangGraph workflows and updates documentation files.

#### Features

- Finds LangGraph graphs in Python files
- Generates Mermaid diagrams
- Updates README.md or other documentation files
- Supports multiple source directories
- Configurable section markers
- Recursive or non-recursive search

#### Usage

Basic usage:
```bash
python scripts/generate_graph_diagrams.py
```

Advanced options:
```bash
# Search in multiple directories
python scripts/generate_graph_diagrams.py --source-dirs src lib tests

# Custom README location
python scripts/generate_graph_diagrams.py --readme docs/README.md

# Custom section markers
python scripts/generate_graph_diagrams.py --start-marker "## Graphs" --end-marker "## API"

# Non-recursive search
python scripts/generate_graph_diagrams.py --source-dirs src --no-recursive
```

#### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--source-dirs` | Source directories to search for graphs | `["src"]` |
| `--readme` | Path to the README file | `README.md` |
| `--start-marker` | Start marker for the graphs section | `## Graph Visualizations` |
| `--end-marker` | End marker for the graphs section | None |
| `--recursive` | Search recursively in source directories | True |

#### Requirements

- Python 3.9+
- LangGraph library
- Mermaid-compatible Markdown viewer

---

## Adding New Scripts

When adding new scripts to this directory, please follow these guidelines:

1. **Naming Convention**
   - Use descriptive, lowercase names with underscores
   - Add `.py` extension for Python scripts
   - Example: `update_version.py`, `generate_docs.py`

2. **Documentation**
   - Add a section to this README following the template below
   - Include detailed docstrings in the script
   - Add usage examples and requirements

3. **Script Structure**
   - Use argparse for command-line arguments
   - Include proper error handling
   - Add type hints
   - Follow the project's code style

### Template for New Script Documentation

```markdown
### Script Name (`script_name.py`)

Brief description of what the script does.

#### Features

- Feature 1
- Feature 2
- Feature 3

#### Usage

Basic usage:
```bash
python scripts/script_name.py
```

Advanced options:
```bash
python scripts/script_name.py --option value
```

#### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--arg1` | Description of arg1 | `default1` |
| `--arg2` | Description of arg2 | `default2` |

#### Requirements

- Requirement 1
- Requirement 2
```

## Best Practices

1. **Testing**
   - Add tests for new scripts in the `tests/scripts` directory
   - Test with different arguments and edge cases
   - Verify script behavior in different environments

2. **Error Handling**
   - Provide clear error messages
   - Handle common failure cases gracefully
   - Add appropriate logging

3. **Documentation**
   - Keep this README up to date
   - Include examples for common use cases
   - Document any breaking changes

4. **Dependencies**
   - List all required dependencies
   - Use project-wide dependencies when possible
   - Document any system requirements

## Contributing

When contributing new scripts:

1. Create a new branch for your script
2. Add the script and update this README
3. Add tests if applicable
4. Submit a pull request
5. Update documentation as needed
