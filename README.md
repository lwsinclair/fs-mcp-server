[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/boleyn-fs-mcp-server-badge.png)](https://mseep.ai/app/boleyn-fs-mcp-server)

# FS-MCP: Universal File Reader & Intelligent Search MCP Server

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-green.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)

**A powerful MCP (Model Context Protocol) server that provides intelligent file reading and semantic search capabilities**

[English](#english) | [中文](#中文)

</div>

---

## English

### 🚀 Features

- **🧠 Intelligent Text Detection**: Automatically identifies text files without relying on file extensions
- **📄 Multi-Format Support**: Handles text files and document formats (Word, Excel, PDF, etc.)
- **🔒 Security First**: Restricted access to configured safe directories only
- **📏 Range Reading**: Supports reading specific line ranges for large files
- **🔄 Document Conversion**: Automatic conversion of documents to Markdown with caching
- **🔍 Vector Search**: Semantic search powered by AI embeddings
- **⚡ High Performance**: Batch processing and intelligent caching support
- **🌐 Multi-language**: Supports both English and Chinese content

### 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [MCP Tools](#mcp-tools)
- [Vector Search](#vector-search)
- [Supported Formats](#supported-formats)
- [Security Features](#security-features)
- [Integration](#integration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

### 🚀 Quick Start

#### 1. Clone and Install

```bash
git clone https://github.com/yourusername/fs-mcp.git
cd fs-mcp
```

**Using uv (Recommended):**
```bash
uv sync
```

**Using pip:**
```bash
pip install -r requirements.txt  # If you have a requirements.txt
# OR install directly
pip install fastmcp>=2.0.0 langchain>=0.3.0 python-dotenv>=1.1.0
```

#### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Security Settings
SAFE_DIRECTORY=.                    # Directory restriction (required)
MAX_FILE_SIZE_MB=100                # File size limit in MB

# Encoding Settings
DEFAULT_ENCODING=utf-8

# AI Embeddings Configuration (for vector search)
OPENAI_EMBEDDINGS_API_KEY=your-api-key
OPENAI_EMBEDDINGS_BASE_URL=http://your-embedding-service/v1
EMBEDDING_MODEL_NAME=BAAI/bge-m3    # Or your preferred model
EMBEDDING_CHUNK_SIZE=1000
```

#### 3. Start the Server

```bash
python main.py
```

The server will start on `http://localhost:3002` and automatically build the vector index.

### 🛠️ Installation

#### System Requirements

- **Python**: 3.12 or higher
- **OS**: Windows, macOS, Linux
- **Memory**: 4GB+ recommended for vector search
- **Storage**: 1GB+ for caching and indexes

#### Dependencies

Core dependencies are managed in `pyproject.toml`:
- `fastmcp>=2.0.0` - MCP server framework
- `langchain>=0.3.0` - AI and vector search
- `python-dotenv>=1.1.0` - Environment management
- Document processing libraries (pandas, openpyxl, python-docx, etc.)

### ⚙️ Configuration

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SAFE_DIRECTORY` | `.` | Root directory for file access |
| `MAX_FILE_SIZE_MB` | `100` | Maximum file size limit |
| `DEFAULT_ENCODING` | `utf-8` | Default file encoding |
| `OPENAI_EMBEDDINGS_API_KEY` | - | API key for embedding service |
| `OPENAI_EMBEDDINGS_BASE_URL` | - | Embedding service URL |
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-m3` | AI model for embeddings |
| `EMBEDDING_CHUNK_SIZE` | `1000` | Text chunk size for processing |

#### Advanced Configuration

For production deployments, consider:
- Setting up rate limiting
- Configuring log rotation
- Using external vector databases
- Setting up monitoring

### 🔧 MCP Tools

#### 1. `view_directory_tree`
**Purpose**: Display directory structure in tree format
```python
view_directory_tree(
    directory_path=".",     # Target directory
    max_depth=3,           # Maximum depth
    max_entries=300        # Maximum entries to show
)
```

#### 2. `read_file_content`
**Purpose**: Read file content with line range support
```python
read_file_content(
    file_path="example.py",  # File path
    start_line=1,           # Start line (optional)
    end_line=50             # End line (optional)
)
```

#### 3. `search_documents`
**Purpose**: Intelligent semantic search across documents
```python
search_documents(
    query="authentication logic",     # Search query
    search_type="semantic",          # semantic/filename/hybrid/extension
    file_extensions=".py,.js",       # File type filter (optional)
    max_results=10                   # Maximum results
)
```

#### 4. `rebuild_document_index`
**Purpose**: Rebuild vector index for search
```python
rebuild_document_index()  # No parameters needed
```

#### 5. `get_document_stats`
**Purpose**: Get index statistics and system status
```python
get_document_stats()  # Returns comprehensive stats
```

#### 6. `list_files`
**Purpose**: List files in directory with pattern matching
```python
list_files(
    directory_path="./src",  # Directory to list
    pattern="*.py",         # File pattern
    include_size=True       # Include file sizes
)
```

#### 7. `preview_file`
**Purpose**: Quick preview of file content
```python
preview_file(
    file_path="example.py",  # File to preview
    lines=20                # Number of lines
)
```

### 🔍 Vector Search

#### Capabilities

- **Semantic Understanding**: Search "user authentication" finds "login verification" code
- **Synonym Recognition**: Search "database" finds "数据库" (Chinese) content
- **Multi-language Support**: Handles English, Chinese, and mixed content
- **Context Awareness**: Understands code semantics and relationships

#### Search Types

1. **Semantic Search** (`semantic`): AI-powered understanding
2. **Filename Search** (`filename`): Fast filename matching
3. **Extension Search** (`extension`): Filter by file type
4. **Hybrid Search** (`hybrid`): Combines semantic + filename

#### Technical Stack

- **Embedding Model**: BAAI/bge-m3 (1024-dimensional vectors)
- **Vector Database**: ChromaDB
- **Text Splitting**: Intelligent semantic chunking
- **Incremental Updates**: Hash-based change detection

### 📁 Supported Formats

#### Auto-detected Text Files
- Programming languages: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, etc.
- Config files: `.json`, `.yaml`, `.toml`, `.ini`, `.xml`, `.env`
- Documentation: `.md`, `.txt`, `.rst`
- Web files: `.html`, `.css`, `.scss`
- Data files: `.csv`, `.tsv`
- Files without extensions (auto-detected)

#### Document Formats (Auto-converted to Markdown)
- **Microsoft Office**: `.docx`, `.xlsx`, `.pptx`
- **OpenDocument**: `.odt`, `.ods`, `.odp`
- **PDF**: `.pdf` (text extraction)
- **Legacy formats**: `.doc`, `.xls` (limited support)

### 🔒 Security Features

#### Access Control
- **Directory Restriction**: Access limited to `SAFE_DIRECTORY` and subdirectories
- **Path Traversal Protection**: Automatic prevention of `../` attacks
- **Symlink Control**: Configurable symbolic link access
- **File Size Limits**: Prevents reading oversized files

#### Validation
- **Path Sanitization**: Automatic path cleaning and validation
- **Permission Checks**: Verify read permissions before access
- **Error Handling**: Graceful failure with informative messages

### 🔗 Integration

#### Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "fs-mcp": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/fs-mcp",
      "env": {
        "SAFE_DIRECTORY": "/your/project/directory"
      }
    }
  }
}
```

#### Other MCP Clients

Connect to `http://localhost:3002` using Server-Sent Events (SSE) protocol.

#### API Integration

The server exposes standard MCP endpoints that can be integrated with any MCP-compatible client.

### 🏗️ Project Structure

```
fs-mcp/
├── main.py                    # Main MCP server
├── src/                       # Core modules
│   ├── __init__.py           # Package initialization
│   ├── file_reader.py        # Core file reading logic
│   ├── security_validator.py # Security and validation
│   ├── text_detector.py      # Intelligent file detection
│   ├── config_manager.py     # Configuration management
│   ├── document_cache.py     # Document caching system
│   ├── file_converters.py    # Document format converters
│   ├── dir_tree.py          # Directory tree generation
│   ├── embedding_config.py   # AI embedding configuration
│   ├── codebase_indexer.py   # Vector indexing system
│   ├── codebase_search.py    # Search engine
│   ├── index_scheduler.py    # Index scheduling
│   └── progress_bar.py       # Progress display utilities
├── tests/                    # Test suite
├── cache/                    # Document cache (auto-created)
├── logs/                     # Log files (auto-created)
├── pyproject.toml           # Project configuration
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

### 💻 Development

#### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/fs-mcp.git
cd fs-mcp

# Install with development dependencies
uv sync --group dev

# OR with pip
pip install -e ".[dev]"
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_file_reader.py
```

#### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

#### Debugging

Monitor logs in real-time:
```bash
tail -f logs/mcp_server_$(date +%Y%m%d).log
```

### 🤝 Contributing

We welcome contributions! Here's how to get started:

#### 1. Fork and Clone
```bash
git clone https://github.com/yourusername/fs-mcp.git
cd fs-mcp
```

#### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

#### 3. Make Changes
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

#### 4. Test Your Changes
```bash
pytest
black src/ tests/
flake8 src/ tests/
```

#### 5. Submit Pull Request
- Describe your changes clearly
- Reference any related issues
- Ensure all tests pass

#### Development Guidelines

- **Code Style**: Follow PEP 8, use Black for formatting
- **Testing**: Maintain test coverage above 80%
- **Documentation**: Update README and docstrings
- **Commits**: Use conventional commit messages
- **Security**: Follow security best practices

### 📋 Roadmap

- [ ] **Enhanced PDF Processing**: Better table and image extraction
- [ ] **More Embedding Models**: Support for local models
- [ ] **Real-time Indexing**: File system watchers
- [ ] **Advanced Search**: Regex, proximity, faceted search
- [ ] **Performance Optimization**: Async processing, caching improvements
- [ ] **Web Interface**: Optional web UI for management
- [ ] **Plugin System**: Custom file type handlers
- [ ] **Enterprise Features**: Authentication, rate limiting, monitoring

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [LangChain](https://github.com/langchain-ai/langchain) - AI integration
- [ChromaDB](https://github.com/chroma-core/chroma) - Vector database
- [BGE-M3](https://huggingface.co/BAAI/bge-m3) - Embedding model

### 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/fs-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fs-mcp/discussions)
- **Documentation**: Check the `docs/` folder (when available)

---

## 中文

### 🚀 功能特点

- **🧠 智能文本检测**: 无需依赖扩展名，自动识别文本文件
- **📄 多格式支持**: 支持文本文件和文档格式（Word、Excel、PDF等）
- **🔒 安全验证**: 只允许读取配置的安全目录中的文件
- **📏 按行读取**: 支持指定行范围读取，便于处理大文件
- **🔄 文档转换**: 自动将文档格式转换为Markdown并缓存
- **🔍 向量搜索**: 基于AI嵌入的语义搜索
- **⚡ 高性能**: 支持批量文件处理和智能缓存
- **🌐 多语言**: 支持中英文内容处理

### 🚀 快速开始

#### 1. 克隆和安装

```bash
git clone https://github.com/yourusername/fs-mcp.git
cd fs-mcp

# 推荐使用 uv
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### 2. 环境配置

创建 `.env` 文件：

```bash
# 安全设置
SAFE_DIRECTORY=.                    # 目录访问限制（必需）
MAX_FILE_SIZE_MB=100                # 文件大小限制（MB）

# 编码设置
DEFAULT_ENCODING=utf-8

# AI嵌入配置（用于向量搜索）
OPENAI_EMBEDDINGS_API_KEY=your-api-key
OPENAI_EMBEDDINGS_BASE_URL=http://your-embedding-service/v1
EMBEDDING_MODEL_NAME=BAAI/bge-m3    # 或您偏好的模型
EMBEDDING_CHUNK_SIZE=1000
```

#### 3. 启动服务器

```bash
python main.py
```

服务器将在 `http://localhost:3002` 启动并自动建立向量索引。

### 🛠️ MCP工具说明

详细的工具使用方法请参考英文部分的 [MCP Tools](#mcp-tools) 章节。

### 🔍 向量搜索功能

- **概念匹配**：搜索"用户认证"能找到"登录验证"相关代码
- **同义词理解**：搜索"database"能找到"数据库"相关内容
- **多语言支持**：同时理解中英文代码和注释
- **上下文理解**：理解代码的语义和上下文关系

### 📁 支持的文件格式

详细的格式支持请参考英文部分的 [Supported Formats](#supported-formats) 章节。

### 🔒 安全特性

- **路径验证**: 只允许访问配置的安全目录及其子目录
- **文件大小限制**: 防止读取过大文件
- **路径遍历防护**: 自动防止 `../` 等路径遍历攻击
- **符号链接控制**: 可配置是否允许访问符号链接

### 🔗 集成方式

#### Claude Desktop集成

在 Claude Desktop 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "fs-mcp": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/fs-mcp",
      "env": {
        "SAFE_DIRECTORY": "/your/project/directory"
      }
    }
  }
}
```

### 💻 开发

#### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/fs-mcp.git
cd fs-mcp

# 安装开发依赖
uv sync --group dev
```

#### 运行测试

```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=src
```

### 🤝 贡献

欢迎贡献代码！请参考英文部分的 [Contributing](#contributing) 章节了解详细信息。

### 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

<div align="center">

**Made with ❤️ for the AI community**

[⬆ Back to top](#fs-mcp-universal-file-reader--intelligent-search-mcp-server)

</div>
