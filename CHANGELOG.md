# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2025-01-12

### Added
- 🎯 Adaptive Thinking Algorithm - Automatically selects THINK_HARD, MEGATHINK, or ULTRATHINK modes based on query complexity
- 🚀 Full Docker integration - All services now run in Docker containers for better isolation and portability
- 📝 Claude Code CLI support - Added configuration guide for using with Claude Code CLI
- 🧩 Missing AI services modules:
  - `embedding_manager.py` - Vector embeddings for semantic search
  - `db_connection_pool.py` - Thread-safe database connection pooling
  - `performance_monitor.py` - System performance metrics collection
  - `adaptive_thinking.py` - Intelligent thinking mode selection
- 🔧 Health endpoint improvements - Better error handling and system status reporting

### Changed
- 📦 MCP server configuration updated to use Docker exec instead of direct node execution
- 🔒 Enhanced error handling in API endpoints
- 📊 Improved performance monitoring with real-time metrics

### Fixed
- 🐛 Fixed missing Python modules that were preventing Docker build
- 🐛 Fixed health endpoint KeyError for missing system_metrics
- 🐛 Fixed parameter compatibility issue in EmbeddingManager
- 🐛 Added missing methods in PerformanceMonitor (get_health_status, increment_counter, record_timing)

### Technical Details
- Added MAFM and Local-File-Organizer integration for enhanced file organization
- Implemented thread-safe database operations with connection pooling
- Added comprehensive performance metrics tracking
- Enhanced LLM integration with 7 Ollama models support

## [2.3.0] - 2025-01-09

### Added
- Web UI dashboard with Korean language support
- Advanced duplicate detection
- Batch operations for multiple files
- Performance analytics dashboard

## [2.2.0] - 2024-12-15

### Added
- Semantic search with vector embeddings
- Real-time file indexing
- Background task management

## [2.1.0] - 2024-11-20

### Added
- LLM-enhanced search capabilities
- Smart file categorization
- MCP protocol support

## [2.0.0] - 2024-10-01

### Added
- Complete rewrite with FastAPI
- Docker support
- Claude Desktop integration

## [1.0.0] - 2024-08-15

### Added
- Initial release
- Basic file search functionality
- SQLite FTS5 integration