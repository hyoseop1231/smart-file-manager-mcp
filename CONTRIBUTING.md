# Contributing to Smart File Manager MCP

First off, thank you for considering contributing to Smart File Manager MCP! It's people like you that make this tool better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Style Guides](#style-guides)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [hyoseop1231@github.com].

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see [Development Setup](#development-setup))
4. Create a new branch for your feature or bugfix
5. Make your changes
6. Test your changes thoroughly
7. Commit your changes (see [Commit Messages](#commit-messages))
8. Push to your fork
9. Submit a Pull Request

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find that you don't need to create one. When you are creating a bug report, please include as many details as possible:

**Bug Report Template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. macOS 14.0]
 - Docker version: [e.g. 24.0.0]
 - Claude Desktop version: [e.g. 1.0.0]
 
**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Any possible implementations
- Why this enhancement would be useful to most users

### Your First Code Contribution

Unsure where to begin? You can start by looking through these issues:

- Issues labeled `good first issue` - these should be relatively simple
- Issues labeled `help wanted` - these are typically more involved

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Setting Up Your Development Environment

1. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/smart-file-manager-mcp.git
   cd smart-file-manager-mcp
   ```

2. **Set up Python environment:**
   ```bash
   cd ai-services
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Set up Node.js environment:**
   ```bash
   cd ../mcp-server
   npm install
   ```

4. **Run tests to ensure everything is working:**
   ```bash
   # Python tests
   cd ../ai-services
   pytest

   # TypeScript tests
   cd ../mcp-server
   npm test
   ```

### Development Workflow

1. **Start services in development mode:**
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

2. **Make your changes**

3. **Run tests:**
   ```bash
   # Python
   docker-compose exec smart-file-manager pytest

   # TypeScript
   cd mcp-server && npm test
   ```

4. **Check code style:**
   ```bash
   # Python
   black . --check --line-length 120
   ruff check .

   # TypeScript
   npm run lint
   ```

## Style Guides

### Python Style Guide

We use [Black](https://black.readthedocs.io/) for code formatting and [Ruff](https://beta.ruff.rs/docs/) for linting.

- Line length: 120 characters
- Use type hints where possible
- Write docstrings for all public functions and classes
- Follow PEP 8 naming conventions

**Example:**
```python
from typing import List, Dict, Optional

def search_files(
    query: str,
    directories: Optional[List[str]] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Search for files using natural language query.
    
    Args:
        query: Natural language search query
        directories: Optional list of directories to search in
        limit: Maximum number of results to return
        
    Returns:
        Dictionary containing search results and metadata
    """
    # Implementation here
    pass
```

### TypeScript Style Guide

We use ESLint with Prettier for TypeScript code.

- Use meaningful variable names
- Prefer `const` over `let`
- Use async/await over promises where possible
- Add JSDoc comments for public functions

**Example:**
```typescript
/**
 * Handles file search requests from Claude Desktop
 * @param params - Search parameters from MCP protocol
 * @returns Search results formatted for MCP
 */
export async function handleSearchFiles(
  params: SearchParams
): Promise<SearchResult> {
  const { query, limit = 50 } = params;
  
  try {
    const results = await searchAPI.search(query, limit);
    return formatResults(results);
  } catch (error) {
    logger.error('Search failed:', error);
    throw new MCPError('Search operation failed');
  }
}
```

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep README.md updated with any new features
- Document all configuration options

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests
- `chore`: Changes to build process or auxiliary tools

### Examples
```
feat(search): add semantic search using embeddings

Implemented vector embeddings for semantic file search using
the nomic-embed-text model. This allows finding conceptually
similar files even when exact keywords don't match.

Closes #123
```

```
fix(api): resolve 422 error in MCP protocol handling

Added raw request handling to bypass Pydantic validation
issues when receiving requests from Claude Desktop.
```

## Pull Request Process

1. **Update Documentation**: Ensure README.md and other docs reflect your changes
2. **Add Tests**: Include tests that cover your changes
3. **Pass All Checks**: Ensure all tests pass and code meets style guidelines
4. **Update CHANGELOG.md**: Add your changes to the Unreleased section
5. **Create PR**: Use the PR template and fill in all sections

### Pull Request Template
```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

## Community

### Getting Help

- Check the [documentation](https://github.com/hyoseop1231/smart-file-manager-mcp/wiki)
- Search [existing issues](https://github.com/hyoseop1231/smart-file-manager-mcp/issues)
- Join our [discussions](https://github.com/hyoseop1231/smart-file-manager-mcp/discussions)
- Ask questions in the issues with the `question` label

### Staying Updated

- Star the repository to get notifications
- Watch the repository for all activity
- Follow the [changelog](CHANGELOG.md) for updates

## Recognition

Contributors who submit accepted PRs will be added to the [Contributors](#) section of the README.

Thank you for contributing to Smart File Manager MCP! 🎉

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>