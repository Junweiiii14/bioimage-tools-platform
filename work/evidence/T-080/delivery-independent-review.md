# T080 delivery independent review — preliminary

Status: Pending final staging and installed UI evidence; no final Accepted yet.
Reviewer: /root/t080_final_review, independent of product implementation.
Product commit: 79b9db9b7ae055bc3354a3582777082729ca8110.

Read release-gate, preflight, release build-manifest, actual installation receipt, payload receipt and verifier implementation, shipped selfcheck receipt and its two original Diagnostics JSON files. Independently hashed the actual setup executable and both original diagnostic reports; each matches its receipt. Setup is 383923941 bytes, SHA256 fcc63932b624a58d904b7f2985395bf4f3233463451b7fcd0a0e03e57ed08c5d. Build compile/installer and installed update report exit 0. Update receipt preserves old and new user sentinel hashes.

Payload verifier checks every built file against installation and compares product Python/web assets against reviewed source, rejecting unexpected installed product sources; it is not merely a manifest-identity check. Selfcheck original reports show passed/errors=[], offline OCR and save/reopen checks, plus 19 supervision checks with real workers, original pixels, display correction, missing-not-zero, output, recovery and owned shutdown. Supervision executable/module paths point to the stable installation and isolated_imports=true. Actual report hashes equal the selfcheck receipt.

No Qt process launched by this reviewer. No claims yet for the separately running installed UI harness, final delivery ZIP/staging completeness, clean Windows machines, all staff hardware or independent scientific project accuracy. Await final artifacts before final verdict.

## Final artifact verdict

Verdict: Accepted (local laboratory delivery, with stated target-machine limits).
Product commit: 79b9db9b7ae055bc3354a3582777082729ca8110.
Archive: WB-79b9db9b7ae0.zip, 397029900 bytes.
Archive SHA256: 525d4a55af3460ec1273bf29e2956a98973e4d569b05e121069ac214bbd9460f.

After installed UI and staging completed, independently read acceptance.json (installed runtime, pytestExit 0, loaded product/Qt module locations and hashes), staging receipts and actual user instructions. Root's installed UI run reports 27 passed in 24.12s; this reviewer did not rerun Qt. Existing SharedImageManager/mailbox diagnostics do not establish GPU-root-cause resolution.

Independently verified the actual ZIP CRC, exact member set and absence of duplicate names, all 201 member SHA256 values against the receipt and actual staging files, their sizes, and the complete ZIP SHA256. Verification exited 0. Initial read-only probe failed on host default GBK JSON decoding; retry explicitly used UTF-8 and bytes parsing, without artifact modification.

The exact installer filename is identified in the first-read guide. The package includes the full installer, checksums and local verifier, installation/use/verification-limit instructions, dependency/environment inventory, source archive, third-party licenses, maintenance evidence and synthetic practice originals plus complete project/recovery ZIP. Practice receipt binds two deterministic synthetic TIFF hashes and full copied project; no private laboratory input is used. Source archive member inspection found no .local or TIFF/PNG media candidates. The practice instructions distinguish display from original quantitative images and retain intentional quality/missing flags.

Readiness is for handing over this verified local package, not proof that all staff machines have been tested. Unsigned installer, per-user installation, Windows x64 target, per-machine selfcheck/practice, unverified clean Windows 10/physical DPI/Explorer input and independent 80%-project scientific accuracy are clearly disclosed. Desktop copy/publication had not occurred during this review: a later copy must match the archive hash above. No new Qt process or product mutation was performed by this reviewer.
