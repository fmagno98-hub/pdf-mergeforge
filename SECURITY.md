# PDF MergeForge Security Policy

Report vulnerabilities privately through GitHub's security advisory feature. Do not
attach confidential PDFs. Supported version: 1.1.x. The app processes documents locally
and does not bypass encryption.

The application has no network client, remote API, cloud upload, telemetry, or
automatic updater. Security reports should never include confidential source PDFs.

PDF/A conversion invokes a separately installed Ghostscript executable. Independent
validation invokes the bundled veraPDF CLI through the bundled Eclipse Temurin runtime.
Both receive local filesystem paths only. PDF MergeForge does not send documents or
validation reports to Artifex, veraPDF, Adoptium, or any other server.
