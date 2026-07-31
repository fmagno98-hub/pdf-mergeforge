# PDF/A-1b export

PDF/A is an ISO-standardised subset of PDF designed for long-term preservation. PDF/A-1
is based on PDF 1.4. Conformance level **B** preserves reliable visual reproduction;
PDF/A-1a additionally requires semantic structure and accessibility information.

A real PDF/A-1b file is more than a PDF with two metadata fields. It must avoid
encryption, embed fonts, use supported colour information and an OutputIntent backed by
an ICC profile, contain correct XMP identification metadata, and avoid features that
PDF/A-1 cannot preserve. Merely setting `pdfaid:part=1` and
`pdfaid:conformance=B` is not sufficient.

## How PDF MergeForge creates it

1. The existing validator checks every selected source PDF.
2. The existing merger combines them in the displayed order into a temporary PDF.
3. A separately installed 64-bit Ghostscript is detected and executed as an external
   process using its own PDF/A definition and sRGB ICC resources.
4. The app requests PDF 1.4, embedded fonts, RGB colour conversion, an OutputIntent,
   and strict failure for incompatible content.
5. Internal baseline checks verify readability, page count, encryption state, XMP
   identification, PDF version, and OutputIntent.
6. If separately installed, veraPDF performs an independent full PDF/A-1b validation.
7. Only a successful candidate atomically replaces the chosen destination.

All work is local. Original files are opened read-only and never modified. Temporary
files are removed after success, failure, or cancellation.

## Installing Ghostscript

1. Open **Export as PDF/A-1b** and choose **Download Ghostscript**.
2. Download the Windows 64-bit installer from the official Ghostscript site.
3. Run the official installer and complete installation.
4. Return to PDF MergeForge and choose **Check again**.
5. If it is not detected, choose **Locate gswin64c.exe**.
6. Select the executable normally found under
   `C:\Program Files\gs\<version>\bin\gswin64c.exe`.

PDF MergeForge checks the executable name and runs `--version` with a timeout before
trusting the selection. It does not download software, change `PATH`, edit the registry,
or request administrator privileges.

## veraPDF

veraPDF is an optional, separately installed validator. Baseline checks are useful
diagnostics but are not equivalent to standards validation. A successful veraPDF
PDF/A-1b result gives stronger technical evidence, but the app never calls the document
“certified”.

Install veraPDF separately from its official release page. On Windows, open **External
tools**, choose **Locate veraPDF**, and select `verapdf.bat`. Custom paths containing
spaces or Unicode are supported. **Check again** repeats discovery; **Validate now**
checks the last export with profile `1b` and a structured JSON report without converting
it again.

- **Passed:** independent veraPDF PDF/A-1b validation succeeded.
- **Not performed:** baseline checks passed but optional veraPDF was not detected.
- **Failed:** veraPDF explicitly reported non-conformance.

The batch launcher runs locally through Windows `cmd.exe` using an argument list,
`shell=False`, a hidden console, and a timeout. PDFs and reports are never sent online.

## Limitations and preservation advice

PDF/A-1 may require transparency flattening or removal/conversion of JavaScript,
multimedia, unsupported annotations, forms, layers, and other interactive features.
Font substitution or colour conversion can change rendering. Digital signatures are
normally invalidated by conversion. Always keep the original files and visually compare
important output pages.

Conformance does not guarantee that every archive, court, regulator, or administrative
body will accept a document. Check the recipient's exact profile and submission rules.

## Troubleshooting

- **Ghostscript not found:** install the 64-bit Windows version, retry, or locate
  `gswin64c.exe` manually.
- **Required resources missing:** repair/reinstall Ghostscript; its PDF/A definition and
  sRGB ICC profile must be present in the external installation.
- **Conversion failed:** the input may contain a feature incompatible with strict
  PDF/A-1b output. The existing destination remains untouched.
- **Baseline validation failed:** no final file is installed; review the local log.
- **veraPDF unavailable:** the file may still be saved after baseline checks, with a clear
  warning that independent validation was not performed.
- **veraPDF reports non-compliance:** the final destination is not replaced.
