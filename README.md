# CopyBoundary

Before copying a project folder, see which symbolic links resolve outside it, which links are broken, and which entries are special files. A tiny original, dependency-free, read-only Python CLI for macOS and Linux.

## Install and run

Requires Python 3.10 or newer. No pip packages.

```sh
git clone https://github.com/00xmorty/copyboundary.git
cd copyboundary
python3 copyboundary /path/to/project
python3 copyboundary /path/to/project --json --max-entries 10000
```

Or download the single-file `copyboundary` asset from the v0.1.0 release and run `python3 copyboundary /path/to/project`. No installation into system folders is needed.

## Minimal example

```sh
mkdir -p demo/project
printf 'example\n' > demo/outside.txt
ln -s ../outside.txt demo/project/link
python3 copyboundary demo/project --json
```

Expected: `status=REVIEW`, one `symlink` finding with `scope=external` and `target_state=present`. Exit 1 is intentional: it requests review, not a program crash. These example commands create only your chosen demo files; the scanner itself writes nothing.

## Output and exit codes

- 0 / `NO_FLAGGED_RISK`: no flagged risks observed, **not proof of a safe copy**. Internal links remain listed.
- 1 / `REVIEW`: external or broken links, or special files need review.
- 2 / `UNKNOWN`: unreadable metadata, cycles, invalid root or entry limit. This takes precedence over REVIEW; inspect all findings.

Each finding includes only a root-relative path and classifications. Symlink destinations and file contents are not printed. Control characters in names are JSON-escaped even in text output. Normal files are counted but not listed. Root symlinks are rejected. The entry cap defaults to 10,000.

## Safety

No copying, deletion, command execution, sudo, settings changes, telemetry or network requests. The scanner enumerates directory entries and reads metadata, never opens file contents or FIFO streams. It does not deliberately recurse into symlink directories. Symlink resolution and stat can inspect metadata outside the root. Reports can still reveal sensitive **relative filenames**: manually review before sharing. Do not scan hostile, concurrently changing trees or untrusted mounted/network filesystems.

## Limitations

This is a preflight snapshot, not a sandbox or secure copier. Files can change between checks; directory replacement races are not prevented. Metadata probes may block on slow mounts; the entry cap is not a wall-clock timeout. Mount points are traversed as ordinary directories; hard links, ACLs, extended attributes, storage accounting and destination behavior are not audited. Filesystem case handling and permission behavior vary. No Windows support claim.

If you intend to preserve symlinks rather than dereference their targets, inspect the native `cp` manual and consider `cp -RP source destination` after independent review. The tool never runs that command. Exact copy behavior depends on flags, implementation and arguments; this utility does not certify it.

Reference: Apple's native cp manual source: https://github.com/apple-oss-distributions/file_cmds/blob/main/cp/cp.1 ; Python path resolution: https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve . No upstream code copied.

## Tests

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile copyboundary
```

CI exercises the tests on macOS and Linux with Python 3.10 and 3.13.

## License

MIT. See LICENSE. See SECURITY.md for reporting security concerns.
