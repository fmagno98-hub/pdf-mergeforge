# GitHub release checklist — v1.1.0

- Keep repository name: `pdf-mergeforge`.
- Suggested description: `Offline Windows PDF merger with optional local PDF/A-1b creation and veraPDF validation.`
- Suggested topics: `pdf`, `pdf-merger`, `pdfa`, `pdfa-1b`, `offline`, `privacy`, `windows`, `pyside6`, `verapdf`.
- Push branch only after reviewing the local commits and diff.
- Let the Windows build workflow complete successfully.
- Create tag `v1.1.0` only after CI succeeds.
- Use `RELEASE_NOTES_V1.1.0.md` as the release description.
- Upload `PDF-MergeForge-v1.1.0-Windows-x64.exe` and `SHA256SUMS.txt`.
- Confirm that the release page links to `THIRD_PARTY_NOTICES.md` and `docs/LICENSING.md`.
- Confirm Ghostscript is described as external and separately licensed.
- Confirm veraPDF and Temurin are described as bundled, separate components.
- Do not claim endorsement or guaranteed acceptance by the Agenzia delle Entrate.
- Confirm the release is unsigned and may trigger Windows SmartScreen.
