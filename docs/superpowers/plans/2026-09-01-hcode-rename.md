# Hcode Complete Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the complete MewCode project identity to Hcode without changing any behavior other than names and their corresponding paths.

**Architecture:** Apply one explicit, byte-preserving, case-aware rename map across source, tests, metadata, and active documentation; then rename the package, state directory, project directory, and executable environment in controlled stages. Preserve a source-only rollback snapshot and compare normalized pre/post AST and file bytes so non-name changes cannot pass unnoticed.

**Tech Stack:** Python 3.11, PowerShell, Conda prefix environments, Hatchling, pytest, standard-library AST/hash tools.

**Spec:** `docs/superpowers/specs/2026-09-01-hcode-rename-design.md`

## Global Constraints

- Brand spelling is exactly `Hcode`; technical identifiers are exactly `hcode`.
- Rename `projects/mewcode-python` to `projects/hcode`, package `mewcode` to `hcode`, and `.mewcode` to `.hcode`.
- Do not preserve old import, CLI, or configuration-path compatibility.
- Do not change Agent behavior, prompts beyond brand names, model settings, tool schemas, permission rules, ports, or dependency versions.
- Do not read, print, or copy values from `.mewcode/config.yaml`; move the directory as an opaque filesystem operation.
- Do not access or migrate `~/.mewcode` or any other user-account data.
- Do not call a real model API or access the network.
- Keep the old Conda prefix untouched; create `.local/envs/hcode` locally and do not delete `.local/envs/mewcode-python`.
- The project has no independent Git repository. Do not initialize Git or make commits; use the approved runtime backup and verification evidence as checkpoints.

---

### Task 1: Record a fresh baseline and create the approved rollback point

**Files:**
- Modify: `docs/open-source-assessment.md`
- Create: `runtime/rename-backups/hcode-20260901-pre-rename/` (generated rollback state)
- Create: `runtime/hcode-rename/ast_signature.py` (generated verification helper)
- Create: `runtime/hcode-rename/before-ast.json` (generated baseline)

**Interfaces:**
- Consumes: current project at `projects/mewcode-python`; current environment at `.local/envs/mewcode-python`.
- Produces: fresh CLI/test evidence, a source-only backup, a SHA-256 manifest, and normalized AST signatures used by Task 5.

- [ ] **Step 1: Verify the current environment and CLI baseline**

Run from the workspace root:

```powershell
$oldProject = (Resolve-Path 'projects\mewcode-python').Path
$oldPython = (Resolve-Path '.local\envs\mewcode-python\python.exe').Path
& $oldPython --version
Push-Location $oldProject
try { & $oldPython -B -m mewcode --help } finally { Pop-Location }
```

Expected: Python 3.11.16; help exits 0 and names the current CLI. Stop on any nonzero exit.

- [ ] **Step 2: Run the complete pre-rename test baseline**

```powershell
$baselineTemp = Join-Path ([System.IO.Path]::GetTempPath()) ("hcode-pre-rename-" + [guid]::NewGuid().ToString('N'))
Push-Location $oldProject
try {
  & $oldPython -B -m pytest -q --basetemp $baselineTemp
  if ($LASTEXITCODE -ne 0) { throw 'Pre-rename pytest baseline failed' }
} finally { Pop-Location }
```

Expected: `685 passed, 3 skipped` and exit code 0. Do not continue if the result differs.

- [ ] **Step 3: Complete the required local open-source assessment**

Replace the template in `docs/open-source-assessment.md` with a concise assessment containing these exact decisions:

```markdown
# Open Source Assessment: Hcode rename

## Scope

- Change: local identity-only rename of the user-supplied project.
- External code acquisition: none.
- New dependencies: none.
- Network research: not required because no repository, package, or implementation is being selected or reused.

## License and provenance

The supplied project has no root license file. This rename does not establish ownership,
grant redistribution rights, or change license status. Publication remains out of scope.

## Security and maintenance

Existing findings in `docs/read-only-code-analysis.md` remain unchanged. The rename must
not be represented as fixing any security issue. Dependency versions and hashes remain fixed.

## Decision

`greenfield` for the rename mechanics only: perform deterministic local identifier and path
changes without copying, integrating, adapting, cloning, or forking external code.

## Reuse boundary

No external concepts or code are required. Only the existing local project is transformed.
```

Verification:

```powershell
rg -n '^## (Scope|License and provenance|Security and maintenance|Decision|Reuse boundary)$' "$oldProject\docs\open-source-assessment.md"
```

Expected: all five headings are present.

- [ ] **Step 4: Create and validate a source-only rollback copy**

```powershell
$workspace = (Resolve-Path '.').Path
$backup = Join-Path $workspace 'runtime\rename-backups\hcode-20260901-pre-rename'
$runtimeRoot = [System.IO.Path]::GetFullPath((Join-Path $workspace 'runtime'))
$backupFull = [System.IO.Path]::GetFullPath($backup)
if (-not $backupFull.StartsWith($runtimeRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw 'Backup path escaped runtime'
}
if (Test-Path -LiteralPath $backupFull) { throw 'Rollback backup already exists; inspect it instead of overwriting it' }
New-Item -ItemType Directory -Path $backupFull -Force | Out-Null
$backupItems = @('mewcode','tests','scripts','src','docs','AGENTS.md','project.md','pyproject.toml','README.md','MEWCODE.md','uv.lock','.gitignore')
foreach ($item in $backupItems) {
  $source = Join-Path $oldProject $item
  if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $backupFull -Recurse }
}
$hashes = Get-ChildItem -LiteralPath $backupFull -Recurse -File | Sort-Object FullName | ForEach-Object {
  [pscustomobject]@{ Path=$_.FullName.Substring($backupFull.Length + 1); Sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash }
}
$hashes | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 (Join-Path $backupFull 'sha256-manifest.json')
if (-not $hashes.Count) { throw 'Rollback backup is empty' }
```

The copy intentionally excludes `.mewcode`, logs, outputs, caches, temporary files, and environments.

- [ ] **Step 5: Add the AST signature helper and capture the baseline**

Create `runtime/hcode-rename/ast_signature.py` with `apply_patch`:

```python
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

REPLACEMENTS = (
    ("mewcode-python", "hcode"),
    ("MewCode", "Hcode"),
    ("MEWCODE", "HCODE"),
    ("mewcode", "hcode"),
)


def normalized(value: str) -> str:
    for old, new in REPLACEMENTS:
        value = value.replace(old, new)
    return value


def collect(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for source_root in (root / "mewcode", root / "hcode", root / "tests"):
        if not source_root.is_dir():
            continue
        for path in sorted(source_root.rglob("*.py")):
            relative = normalized(path.relative_to(root).as_posix())
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            dump = normalized(ast.dump(tree, annotate_fields=True, include_attributes=False))
            result[relative] = hashlib.sha256(dump.encode("utf-8")).hexdigest()
    return result


if __name__ == "__main__":
    project = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(collect(project), indent=2, sort_keys=True), encoding="utf-8")
```

Run:

```powershell
$helperRoot = Join-Path $workspace 'runtime\hcode-rename'
& $oldPython -B (Join-Path $helperRoot 'ast_signature.py') $oldProject (Join-Path $helperRoot 'before-ast.json')
```

Expected: JSON contains signatures for 175 Python files under the package and tests.

**Checkpoint:** report the baseline result and backup location. No Git commit is permitted.

---

### Task 2: Establish a failing brand-identity assertion and mark the project in progress

**Files:**
- Modify: `tests/test_commands.py:369`
- Modify: `project.md`

**Interfaces:**
- Consumes: existing `/status` command behavior and pre-rename project state.
- Produces: one failing assertion that turns green only when the visible brand changes, plus durable handoff status before `AGENTS.md` changes.

- [ ] **Step 1: Change the existing status assertion to the approved brand**

Use `apply_patch` to change only:

```python
assert "MewCode 状态" in ui.messages[0]
```

to:

```python
assert "Hcode 状态" in ui.messages[0]
```

- [ ] **Step 2: Run the focused test and verify the expected failure**

```powershell
Push-Location $oldProject
try {
  & $oldPython -B -m pytest -q tests/test_commands.py -k status
  if ($LASTEXITCODE -eq 0) { throw 'Brand assertion unexpectedly passed before implementation' }
} finally { Pop-Location }
```

Expected: failure because the current UI still emits the old brand; no unrelated test failure.

- [ ] **Step 3: Update project handoff state before modifying AGENTS.md**

Use `apply_patch` to set `Status` to `renaming` and append these facts:

- Decision: full rename to Hcode/hcode with no compatibility alias and no behavior changes.
- Progress: design approved; fresh baseline and rollback snapshot completed.
- Next action: deterministic content and path rename.
- Blocker: none.
- Verification: record the exact fresh baseline output and backup manifest count from Task 1.

Do not remove earlier provenance or verification history at this stage; the mechanical rename in Task 3 will update its identifiers.

**Checkpoint:** review the two-file change manually. No Git commit is permitted.

---

### Task 3: Apply the deterministic content rename and rename project-internal paths

**Files:**
- Create: `runtime/hcode-rename/rename_project.py` (generated mechanical helper)
- Modify: every UTF-8 project file containing an approved old-name token, excluding `.mewcode`, generated directories, and `docs/superpowers/`
- Rename: `mewcode/` to `hcode/`
- Rename: `.mewcode/` to `.hcode/`
- Rename: `MEWCODE.md` to `HCODE.md`

**Interfaces:**
- Consumes: exact mapping in the approved spec and the failing brand assertion from Task 2.
- Produces: internally consistent Hcode source, tests, metadata, runtime paths, and documentation while keeping the executable project root unchanged until Task 4.

- [ ] **Step 1: Create the byte-preserving rename helper**

Create `runtime/hcode-rename/rename_project.py` with `apply_patch`:

```python
from __future__ import annotations

import sys
from pathlib import Path

REPLACEMENTS = (
    (b"mewcode-python", b"hcode"),
    (b"MewCode", b"Hcode"),
    (b"MEWCODE", b"HCODE"),
    (b"mewcode", b"hcode"),
)
SKIP_PARTS = {
    ".mewcode",
    ".pytest_cache",
    "__pycache__",
    "logs",
    "outputs",
    "tmp",
    "superpowers",
}


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    changed: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.relative_to(root).parts):
            continue
        raw = path.read_bytes()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        updated = raw
        for old, new in REPLACEMENTS:
            updated = updated.replace(old, new)
        if updated != raw:
            path.write_bytes(updated)
            changed.append(path.relative_to(root).as_posix())
    print(f"changed_files={len(changed)}")
    for name in changed:
        print(name)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the mechanical content transformation**

```powershell
& $oldPython -B (Join-Path $helperRoot 'rename_project.py') $oldProject
if ($LASTEXITCODE -ne 0) { throw 'Content rename failed' }
```

Review the emitted file list. It must contain source, tests, `pyproject.toml`, `uv.lock`, `AGENTS.md`, `project.md`, README, and active docs, but must not contain `.mewcode/config.yaml` or anything under `docs/superpowers/`.

- [ ] **Step 3: Validate and rename the three internal paths**

```powershell
$packageSource = Join-Path $oldProject 'mewcode'
$packageTarget = Join-Path $oldProject 'hcode'
$configSource = Join-Path $oldProject '.mewcode'
$configTarget = Join-Path $oldProject '.hcode'
$readmeSource = Join-Path $oldProject 'MEWCODE.md'
$readmeTarget = Join-Path $oldProject 'HCODE.md'
foreach ($pair in @(@($packageSource,$packageTarget), @($configSource,$configTarget), @($readmeSource,$readmeTarget))) {
  if (-not (Test-Path -LiteralPath $pair[0])) { throw "Rename source missing: $($pair[0])" }
  if (Test-Path -LiteralPath $pair[1]) { throw "Rename target exists: $($pair[1])" }
  if (-not ([System.IO.Path]::GetFullPath($pair[1]).StartsWith($oldProject + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase))) {
    throw "Rename target escaped project: $($pair[1])"
  }
}
Move-Item -LiteralPath $packageSource -Destination $packageTarget
Move-Item -LiteralPath $configSource -Destination $configTarget
Move-Item -LiteralPath $readmeSource -Destination $readmeTarget
```

The configuration directory is moved without reading or rewriting its contents.

- [ ] **Step 4: Run syntax and focused brand verification from the unchanged project root**

```powershell
Push-Location $oldProject
try {
  & $oldPython -B -c "import ast,pathlib; files=list(pathlib.Path('hcode').rglob('*.py'))+list(pathlib.Path('tests').rglob('*.py')); [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in files]; print(f'ast_files={len(files)}')"
  if ($LASTEXITCODE -ne 0) { throw 'AST verification failed' }
  & $oldPython -B -m pytest -q tests/test_commands.py -k status
  if ($LASTEXITCODE -ne 0) { throw 'Focused brand test failed' }
  & $oldPython -B -m hcode --help
  if ($LASTEXITCODE -ne 0) { throw 'Renamed module CLI failed' }
} finally { Pop-Location }
```

Expected: 175 parsed Python files, focused test passes, and help names Hcode/hcode.

**Checkpoint:** compare `hcode/` and `tests/` against the rollback copy after applying the approved mapping in memory. Any other code difference blocks Task 4.

---

### Task 4: Move the workspace project and construct the renamed executable environment

**Files:**
- Rename: `projects/mewcode-python/` to `projects/hcode/`
- Create: `.local/envs/hcode/` by offline clone
- Modify in new environment only: editable distribution metadata and console script

**Interfaces:**
- Consumes: internally renamed project from Task 3 and the approved old environment.
- Produces: final workspace path, importable `hcode` package, `hcode` console script, and unchanged locked dependencies.

- [ ] **Step 1: Resolve and validate the project move**

```powershell
$workspace = (Resolve-Path '.').Path
$projectsRoot = (Resolve-Path 'projects').Path
$projectSource = [System.IO.Path]::GetFullPath((Join-Path $projectsRoot 'mewcode-python'))
$projectTarget = [System.IO.Path]::GetFullPath((Join-Path $projectsRoot 'hcode'))
if ($projectSource -ne $oldProject) { throw 'Resolved source changed unexpectedly' }
if (-not $projectTarget.StartsWith($projectsRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Project target escaped projects root' }
if (-not (Test-Path -LiteralPath $projectSource)) { throw 'Project source missing' }
if (Test-Path -LiteralPath $projectTarget) { throw 'Project target already exists' }
```

- [ ] **Step 2: Move the project directory**

```powershell
Move-Item -LiteralPath $projectSource -Destination $projectTarget
$newProject = (Resolve-Path 'projects\hcode').Path
if (Test-Path -LiteralPath 'projects\mewcode-python') { throw 'Old project path still exists' }
```

- [ ] **Step 3: Clone the locked environment without network access**

```powershell
$oldEnv = (Resolve-Path '.local\envs\mewcode-python').Path
$newEnv = [System.IO.Path]::GetFullPath((Join-Path $workspace '.local\envs\hcode'))
$localEnvs = [System.IO.Path]::GetFullPath((Join-Path $workspace '.local\envs'))
if (-not $newEnv.StartsWith($localEnvs + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'New environment escaped .local/envs' }
if (Test-Path -LiteralPath $newEnv) { throw 'New Hcode environment already exists' }
conda create --offline --yes --prefix $newEnv --clone $oldEnv
if ($LASTEXITCODE -ne 0) { throw 'Conda environment clone failed' }
$newPython = (Resolve-Path (Join-Path $newEnv 'python.exe')).Path
```

- [ ] **Step 4: Replace only the cloned editable project installation**

```powershell
& $newPython -B -m pip uninstall --yes mewcode
if ($LASTEXITCODE -ne 0) { throw 'Old editable distribution removal failed in clone' }
& $newPython -B -m pip install --no-deps --no-build-isolation --editable $newProject
if ($LASTEXITCODE -ne 0) { throw 'Renamed editable install failed' }
& $newPython -B -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
```

Do not run upgrade commands. Do not alter or delete `$oldEnv`.

- [ ] **Step 5: Verify both renamed entry points**

```powershell
Push-Location $newProject
try {
  & $newPython -B -m hcode --help
  if ($LASTEXITCODE -ne 0) { throw 'python -m hcode failed' }
  & (Join-Path $newEnv 'Scripts\hcode.exe') --help
  if ($LASTEXITCODE -ne 0) { throw 'hcode console script failed' }
  & $newPython -B -c "import hcode, hcode.agent, hcode.app, hcode.client, hcode.remote, hcode.tools; print('core imports OK')"
  if ($LASTEXITCODE -ne 0) { throw 'Core import check failed' }
  & $newPython -B -c "import importlib.util; assert importlib.util.find_spec('mewcode') is None; print('old import absent')"
  if ($LASTEXITCODE -ne 0) { throw 'Old import compatibility remains' }
} finally { Pop-Location }
```

**Checkpoint:** record the new Python version, `pip check`, both help exits, and core import result. No Git commit is permitted.

---

### Task 5: Prove behavioral equivalence, sanitize historical task docs, and complete handoff

**Files:**
- Modify: `projects/hcode/project.md`
- Modify mechanically at finalization: `projects/hcode/docs/superpowers/specs/2026-09-01-hcode-rename-design.md`
- Modify mechanically at finalization: `projects/hcode/docs/superpowers/plans/2026-09-01-hcode-rename.md`
- Create: `runtime/hcode-rename/after-ast.json`
- Create: `runtime/hcode-rename/compare_normalized.py`

**Interfaces:**
- Consumes: backup and baseline signatures from Task 1; renamed project/environment from Task 4.
- Produces: proof that code differences are rename-only, complete test evidence, zero active old-name references, and resumable Hcode project state.

- [ ] **Step 1: Generate and compare normalized AST signatures**

```powershell
& $newPython -B (Join-Path $helperRoot 'ast_signature.py') $newProject (Join-Path $helperRoot 'after-ast.json')
& $newPython -B -c "import json,pathlib; p=pathlib.Path(r'$helperRoot'); before=json.loads((p/'before-ast.json').read_text(encoding='utf-8')); after=json.loads((p/'after-ast.json').read_text(encoding='utf-8')); assert before==after, {'missing':sorted(before.keys()-after.keys()),'extra':sorted(after.keys()-before.keys()),'changed':sorted(k for k in before.keys()&after.keys() if before[k]!=after[k])}; print(f'normalized_ast_equal={len(after)}')"
```

Expected: equality for all 175 package/test Python files.

- [ ] **Step 2: Add and run normalized byte comparison for executable project files**

Create `runtime/hcode-rename/compare_normalized.py` with `apply_patch`:

```python
from __future__ import annotations

import sys
from pathlib import Path

REPLACEMENTS = (
    (b"mewcode-python", b"hcode"),
    (b"MewCode", b"Hcode"),
    (b"MEWCODE", b"HCODE"),
    (b"mewcode", b"hcode"),
)
PAIRS = (
    ("mewcode", "hcode"),
    ("tests", "tests"),
    ("scripts", "scripts"),
    ("src", "src"),
)
FILES = (
    ("pyproject.toml", "pyproject.toml"),
    ("uv.lock", "uv.lock"),
    (".gitignore", ".gitignore"),
    ("MEWCODE.md", "HCODE.md"),
)


def mapped(raw: bytes) -> bytes:
    for old, new in REPLACEMENTS:
        raw = raw.replace(old, new)
    return raw


def compare_file(before: Path, after: Path, failures: list[str]) -> None:
    if not before.is_file() or not after.is_file():
        failures.append(f"missing:{before}:{after}")
        return
    if mapped(before.read_bytes()) != after.read_bytes():
        failures.append(f"changed:{after}")


def main() -> None:
    backup = Path(sys.argv[1]).resolve()
    project = Path(sys.argv[2]).resolve()
    failures: list[str] = []
    checked = 0
    for old_dir, new_dir in PAIRS:
        source = backup / old_dir
        target = project / new_dir
        if not source.exists() and not target.exists():
            continue
        for before in sorted(source.rglob("*")):
            if not before.is_file() or "__pycache__" in before.parts:
                continue
            relative = before.relative_to(source)
            compare_file(before, target / relative, failures)
            checked += 1
    for old_name, new_name in FILES:
        compare_file(backup / old_name, project / new_name, failures)
        checked += 1
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"normalized_files_equal={checked}")


if __name__ == "__main__":
    main()
```

Run:

```powershell
& $newPython -B (Join-Path $helperRoot 'compare_normalized.py') $backupFull $newProject
if ($LASTEXITCODE -ne 0) { throw 'Non-name executable file changes detected' }
```

- [ ] **Step 3: Parse the migrated project configuration without displaying values**

```powershell
Push-Location $newProject
try {
  & $newPython -B -c "from hcode.config import load_config; from hcode.client import create_client; c=load_config(); p=c.providers[0]; create_client(p); print(p.protocol, p.model)"
  if ($LASTEXITCODE -ne 0) { throw 'Renamed configuration/client construction failed' }
} finally { Pop-Location }
```

Expected: current protocol and model identifiers only; no API key output and no request.

- [ ] **Step 4: Run the complete post-rename test suite**

```powershell
$finalTemp = Join-Path ([System.IO.Path]::GetTempPath()) ("hcode-post-rename-" + [guid]::NewGuid().ToString('N'))
Push-Location $newProject
try {
  & $newPython -B -m pytest -q --basetemp $finalTemp
  if ($LASTEXITCODE -ne 0) { throw 'Post-rename pytest failed' }
} finally { Pop-Location }
```

Expected: exactly `685 passed, 3 skipped`, with no new warnings.

- [ ] **Step 5: Finalize project.md with evidence**

Use `apply_patch` to set `Status` back to `active` and add:

- Decision: Hcode/hcode is the sole active identity; no old compatibility aliases.
- Progress: source, tests, package, CLI, configuration directory, project directory, docs, and environment renamed.
- Next action: begin the separately scoped P0/P1 security remediation.
- Blockers: real-provider and remote end-to-end tests still require explicit authorization and test credentials.
- Verification: normalized AST/file equality, exact pytest result, both CLI checks, imports, config construction, `pip check`, and workspace handoff results.

- [ ] **Step 6: Apply the approved name map to the now-completed spec and plan**

The Task 3 helper intentionally skipped `docs/superpowers/` so later steps retained executable old-path instructions. Now run a final byte replacement only on the two completed task documents:

```powershell
& $newPython -B -c "from pathlib import Path; files=[Path(r'$newProject')/'docs/superpowers/specs/2026-09-01-hcode-rename-design.md',Path(r'$newProject')/'docs/superpowers/plans/2026-09-01-hcode-rename.md']; reps=[(b'mewcode-python',b'hcode'),(b'MewCode',b'Hcode'),(b'MEWCODE',b'HCODE'),(b'mewcode',b'hcode')]; [(lambda p: p.write_bytes(__import__('functools').reduce(lambda d,r:d.replace(*r),reps,p.read_bytes())))(p) for p in files]"
if ($LASTEXITCODE -ne 0) { throw 'Final task-document rename failed' }
```

This is the last mechanical content transformation; do not use the rewritten plan as an executable rollback recipe. The unchanged original remains in the approved runtime backup.

- [ ] **Step 7: Verify zero old identity in the active project**

```powershell
$oldContentHits = @(rg --no-ignore -i -l 'mewcode' $newProject -g '!logs/**' -g '!outputs/**' -g '!tmp/**' -g '!.pytest_cache/**' -g '!**/__pycache__/**')
$oldPathHits = @(Get-ChildItem -LiteralPath $newProject -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\(logs|outputs|tmp|\.pytest_cache|__pycache__)\\' -and $_.Name -match '(?i)mewcode' })
if ($oldContentHits.Count -or $oldPathHits.Count) {
  $oldContentHits
  $oldPathHits | ForEach-Object FullName
  throw 'Old active identity remains'
}
```

Expected: zero content files and zero paths.

- [ ] **Step 8: Run workspace handoff and final self-review**

```powershell
python -B capabilities/tools/workspace.py handoff hcode
if ($LASTEXITCODE -ne 0) { throw 'Workspace handoff failed' }
python -B capabilities/tools/workspace.py doctor hcode
if ($LASTEXITCODE -ne 0) { throw 'Workspace doctor failed' }
```

Review the packet against:

- the rollback SHA-256 manifest;
- normalized AST and file equality results;
- `685 passed, 3 skipped`;
- zero old-name findings;
- old environment still present;
- no real API call, secret output, dependency version change, or source behavior change.

**Final checkpoint:** report changed paths, verification evidence, rollback locations, and the deliberate non-migration of user-home state. No Git commit is permitted.
