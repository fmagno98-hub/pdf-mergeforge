# Privacy: local by design

PDF MergeForge processes documents entirely on the user's Windows computer.

## What the application does

- Opens only PDF files explicitly selected or dropped by the user.
- Reads source PDFs without modifying them.
- Combines pages in memory using the bundled `pypdf` library.
- Writes a temporary file in the user-selected destination folder.
- Atomically replaces the final output only after verification.
- Deletes the temporary output after cancellation or failure.
- Stores only window geometry and the last open/save folders in local `QSettings`.
- Stores technical error logs locally under `%LOCALAPPDATA%\PDF MergeForge\logs`.
- For optional PDF/A export, executes a separately installed Ghostscript process locally.
- If available, executes a separately installed veraPDF validator locally.
- Stores only manually selected external-tool paths in local `QSettings`.

Ghostscript and veraPDF operate on local files through locally installed command-line
applications. PDF MergeForge does not upload documents to Ghostscript, Artifex,
veraPDF, or any other server.

## What the application does not do

- No uploads and no cloud processing.
- No HTTP requests, sockets, remote APIs, accounts, subscriptions, or API keys.
- No analytics, advertising, telemetry, tracking, or automatic updates.
- No document contents or file history are sent anywhere.
- The official Ghostscript download page opens only after an explicit user click. No
  document names, paths, metadata, logs, or statistics are transmitted by the app.

The portable executable includes the Python runtime, PySide6, pypdf, application
code, and brand assets required for normal merging. Ghostscript, veraPDF, Java, ICC
profiles, and their resources are not bundled. Internet access is not required for
processing; the browser is opened only when the user requests an official download page.

## User responsibility

The software is provided as-is, without warranty. Users are responsible for keeping
backups, choosing appropriate source and destination files, checking the merged PDF,
and complying with laws and third-party rights applicable to their documents. See
`LICENSE` for the legally controlling warranty and liability disclaimer.
