# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Refactored `engine_reference.py` with safe rule parsing, JSON-serializable state, and comprehensive logging
- Hardened `tss_crypto.py` with full type annotations and clear error messages when secretsharing is missing
- Test suite including:
  - `tests/test_smoke.py` - Basic functionality tests
  - `tests/test_tss_crypto.py` - TSS crypto functionality tests
  - `tests/test_api_smoke.py` - API endpoint smoke tests
- Enhanced CI workflow (`.github/workflows/python-app.yml`) with:
  - Pip dependency caching for faster builds
  - Black code formatting checks
  - Conditional pytest execution
- `pyproject.toml` for modern Python project configuration
- `.pre-commit-config.yaml` for automated pre-commit checks
- `.gitignore` to exclude build artifacts and temporary files
- Comprehensive `README.md` with setup and usage instructions
- `CONTRIBUTING.md` with contribution guidelines
- `CHANGELOG.md` for tracking project history

### Changed
- Replaced unsafe `eval()` in rule parsing with safe condition evaluation
- Changed state storage from using sets to lists for JSON serialization compatibility
- Enhanced error handling throughout the codebase
- Improved function signatures with complete type annotations
- Added descriptive docstrings to all public functions

### Security
- Removed unsafe `eval()` usage in rule condition evaluation
- Added `SecretSharingUnavailableError` with clear installation instructions
- Enhanced logging for audit trails
- Improved error messages to prevent information leakage

### Fixed
- JSON serialization issues with set types in session state
- Missing error handling in TSS endpoints

## [1.0.0] - 2025-10-21

### Added
- Initial release with FastAPI-based interactive course platform
- Threshold Secret Sharing (TSS) implementation
- Adaptive questionnaire system
- Basic CI/CD with GitHub Actions
- Docker support

[Unreleased]: https://github.com/asforalimathiago-art/interactive-course-tss/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/asforalimathiago-art/interactive-course-tss/releases/tag/v1.0.0
