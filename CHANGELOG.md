# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased
### Added
- server.py is the script for remote access to PA

### Changed
- main.py is rewritten using Twisted

## [0.2.0] - 2018-08-31
### Added
- Configuration parser
- Travis-CI integration
- Codecov integration
- Bettercodehub integration
- translator submodule
- Kapellmeister class

### Changed
- Kapellmeister is now used in main.py instead of Runner
- translator socket is now sent to brain process

## 0.1.0 - 2018-08-19
### Added
- readme
- license
- This changelog
- requirements.txt and requirements-dev.txt
- main.py is the script for local access to PA
- utils.py with utility functions
- pa_brain submodule

[Unreleased]: https://github.com/aragaer/pa-core/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/aragaer/pa-core/compare/v0.1.0...v0.2.0
