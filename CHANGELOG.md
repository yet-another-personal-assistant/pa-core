# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- local.py script

### Changed
- Using brain 0.4.0 now

### Fixed
- FakeBrain is now line-buffered as it should be
- FakeBrain now sends messages with correct "from" field

## [0.3.0] - 2018-11-05
### Added
- server.py is the script for remote access to PA
- terminate in Kapellmeister

### Changed
- main.py is rewritten using Twisted
- pa2human submodule updated to version 0.2.0
- pa_brain submodule updated to version 0.3.0

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

[Unreleased]: https://github.com/aragaer/pa-core/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/aragaer/pa-core/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/aragaer/pa-core/compare/v0.1.0...v0.2.0
