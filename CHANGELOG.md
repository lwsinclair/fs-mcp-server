# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial open source release preparation
- Comprehensive README with English and Chinese documentation
- Contributing guidelines and development setup instructions
- GitHub Actions CI/CD pipeline
- Security scanning with bandit
- Code quality checks with black, flake8, and mypy

## [0.1.0] - 2024-01-XX

### Added
- **Core File Reading Features**
  - Universal file reader with intelligent text detection
  - Support for multiple file formats (text files, documents)
  - Line-range reading for large files
  - Document conversion to Markdown with caching
  - Security validation for file access

- **Vector Search Capabilities**
  - Semantic search powered by AI embeddings
  - Multiple search types: semantic, filename, extension, hybrid
  - ChromaDB vector database integration
  - Automatic index building and maintenance
  - Support for multilingual content (English/Chinese)

- **MCP Server Integration**
  - FastMCP 2.0 server implementation
  - RESTful API with Server-Sent Events (SSE)
  - Claude Desktop integration support
  - Comprehensive error handling and logging

- **Document Processing**
  - Microsoft Office formats (.docx, .xlsx, .pptx)
  - PDF text extraction
  - OpenDocument formats (.odt, .ods)
  - Intelligent caching system with MD5 verification

- **Security Features**
  - Directory access restriction
  - Path traversal protection
  - File size limitations
  - Permission validation

- **Developer Experience**
  - Comprehensive logging system
  - Progress bars for long operations
  - Configurable environment variables
  - Automatic startup indexing

### Technical Stack
- Python 3.12+ support
- FastMCP 2.0 framework
- LangChain for AI integration
- ChromaDB for vector storage
- BAAI/bge-m3 embedding model
- Comprehensive test suite

### Infrastructure
- UV package manager support
- Docker-ready configuration
- Automated testing and quality checks
- Documentation and examples

---

## Release Notes Format

### Added
- New features and capabilities

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements and vulnerability fixes 