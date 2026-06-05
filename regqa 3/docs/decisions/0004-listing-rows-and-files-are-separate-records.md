# 4. Listing rows and files are separate records

Status: accepted
Date: 2026-08-29

## Context

The circulars listing page carries a reference number, an issue date and a title
for every document. None of that is recoverable from the PDF URL: filenames are
opaque upload timestamps, and they do not correspond to document dates. The row
dated 26 Apr 2019 links to 191105290352_1.pdf.

The listing is therefore primary evidence about a document, not a way of finding
one. Phase 3 has to weigh a date taken from the listing against a date extracted
from the document body, and cannot do that if the two were merged on ingest.

## Decision

Two tables. `source_listing` holds what the institute published about a document.
`raw_document` holds bytes identified by SHA-256. A listing row points at a
document; several rows may point at the same one.

## Alternatives considered

- **One table with nullable columns.** Fewer joins. Rejected because it discards
  the distinction between what the site claimed and what we downloaded, which is
  the distinction Phase 3 depends on.
- **URL as identity.** Rejected: filenames are unstable and the same document can
  appear at more than one URL.

## Consequences

- Re-running a crawl is free: identical bytes hash to a path that already exists.
- Reference numbers are not unique. NITR/ES/2013/M/2065 appears on two different
  documents, so the uniqueness constraint uses (source, document_url, title,
  issued_on) with NULLS NOT DISTINCT instead.
- A listing row can exist with no file, which is the correct representation of a
  broken link rather than an error.
