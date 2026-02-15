# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-16

### Fixed
- Fixed `test_auto_ingest_flow` failing due to missing async support.
- Migrated deprecated `datetime.utcnow()` calls to `datetime.now(timezone.utc)`.
- Updated `pyproject.toml` license field to use modern SPDX string format.

### Changed
- Improved resilience of ingestion logic against missing metadata.

## [1.0.0] - 2026-02-11

### Added
- Initial release of OpenMemX.
- Semantic memory stack with LanceDB integration.
- GraphRAG support for hierarchical context.
- Bayes-Surprise calculation for token optimization.
- MCP Server integration for standard agent communication.
