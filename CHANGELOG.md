# Changelog

Since `0.3.0`, all new release changelogs will be posted here in addition to their [release pages](https://github.com/vrnavi/sangou/releases).

- This changelog's format __***`roughly`***__ follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
- This project's version format __***`roughly`***__ follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2](https://github.com/vrnavi/sangou/releases/tag/0.3.2) - 2024-02-08

### Fixed
- Fixed the Reply Ping system being broken.
- Fixed command argument errors not showing the full command.
- Fixed error message viewing by using message slicing better.

## [0.3.1](https://github.com/vrnavi/sangou/releases/tag/0.3.1) - 2024-02-06

### Added
- Debugging tools. Don't worry about it.

### Fixed
- Fixed checks being out of order.
- Fixed prefix and alias checking assuming profile entries exist.
- Fixed alias and prefix commands stepping over each other, causing prefix to break.

## [0.3.0](https://github.com/vrnavi/sangou/releases/tag/0.3.0) - 2024-02-05

### Added
- `pls tossed` - Aliases to `pls sessions`, use in a toss channel to see who the bot sees as tossed.
- `pls alert` - Staff command. Waits for a given member's next message, and pings you with it.
- `pls diff` - Diffs between two strings, or two files. Implemented by @OblivionCreator in https://github.com/vrnavi/sangou/pull/29.
- `pls google` - Googles the given argument for you.
- `pls temp`/`temperature` - Converts between Celsius, Fahrenheit, and Kelvin.
- `pls jump` - Jumps to the start of the current channel.
- Command Permission Overrides - Available in the server configuration. Allows server admins to allow also or only allow a command for certain roles.
- Command Aliasing - Accessible from `pls alias`. Allows users to alias commands to a custom string.
- Randoms - `pls peppino`/`noise`/`gustavo`/`rat`/`bench` will post a random whatever, respectively.

### Changed
- Please Reply Ping will now keep its ping to the replied user until said user sends their next message, to prevent ghost pings.
- Self Assignable Roles are now configured through the server configuration rather than `pls tsar`.
- Features requiring server configuration will now check if roles/channels/categories actually exist before continuing.
- Server configuration is now checked against `config.schema.yml` rather than a `stock_config` in the helper file.
- Archive overviews now show a sensible size format.
- Joingraph and progessbar now use in-memory files rather than actual files.
- Progressbar now corresponds to your configured timezone.
- `pls hash` now spits out CRC32 alongside MD5 and SHA1.
- Quoting a message will now spoiler its image if its spoilered originally.
- Updated the README to look nicer. I should probably add a proper changelog file soon.

### Fixed
- Fixed `pls purge emoji` not actually purging emoji.
- Fixed `pls purge bots` not actually purging bots.
- Fixed role changes not appearing in the user logs.
- Fixed forum channel default emoji changes appearing twice in the server logs.
- Fixed translation reactions tripping on empty messages.

### Removed
- Removed Yongou.
