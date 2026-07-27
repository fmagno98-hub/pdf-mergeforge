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

## What the application does not do

- No uploads and no cloud processing.
- No HTTP requests, sockets, remote APIs, accounts, subscriptions, or API keys.
- No analytics, advertising, telemetry, tracking, or automatic updates.
- No document contents or file history are sent anywhere.

The portable executable includes the Python runtime, PySide6, pypdf, application
code, and brand assets required to run offline. Internet access is not required.

## User responsibility

The software is provided as-is, without warranty. Users are responsible for keeping
backups, choosing appropriate source and destination files, checking the merged PDF,
and complying with laws and third-party rights applicable to their documents. See
`LICENSE` for the legally controlling warranty and liability disclaimer.
