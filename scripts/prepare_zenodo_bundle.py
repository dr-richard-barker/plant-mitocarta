#!/usr/bin/env python3
"""
Zenodo Release Packaging Script for Plant MitoCarta.

Creates a clean, reproducible zip archive and tarball in dist/ containing:
- Published Catalog & Sidecars (catalog/)
- Ontology Specifications & Entity Records (ontology/)
- Compiled Maps (docs/maps/*.svg, docs/maps/*.sbgn)
- Bioinformatics & Systems Biology Bulk Downloads (docs/downloads/*.tsv, *.gmt, *.cyjs)
- Python Package Source Code (src/plant_mitocarta/)
- Evidence Base & References (evidence/)
- Release Metadata, Licenses, and Checksums (.zenodo.json, CITATION.cff, LICENSE, LICENSE-DATA, MANIFEST.tsv, CHECKSUMS.sha256)
"""
import hashlib
import json
import pathlib
import sys
import zipfile
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"


def compute_sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    with open(ROOT / ".zenodo.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    version = meta.get("version", "0.1.0")
    bundle_name = f"plant_mitocarta_v{version}_zenodo"
    zip_path = DIST_DIR / f"{bundle_name}.zip"
    tar_path = DIST_DIR / f"{bundle_name}.tar.gz"

    # Directories and files to include
    include_paths = [
        ".zenodo.json",
        "CITATION.cff",
        "LICENSE",
        "LICENSE-DATA",
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "MANIFEST.tsv",
        "CHECKSUMS.sha256",
        "catalog",
        "ontology",
        "maps/src",
        "docs/maps",
        "docs/downloads",
        "src/plant_mitocarta",
        "evidence",
        "results",
    ]

    files_to_pack = []
    for p_str in include_paths:
        p = ROOT / p_str
        if p.is_file():
            files_to_pack.append(p)
        elif p.is_dir():
            for sub_p in p.rglob("*"):
                if sub_p.is_file() and not sub_p.name.startswith("."):
                    files_to_pack.append(sub_p)

    files_to_pack = sorted(list(set(files_to_pack)), key=lambda x: str(x))

    # 1. Build ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in files_to_pack:
            arcname = str(fp.relative_to(ROOT))
            zf.write(fp, arcname=f"{bundle_name}/{arcname}")

    zip_sha = compute_sha256(zip_path)
    zip_size_kb = zip_path.stat().st_size / 1024

    # 2. Build TAR.GZ
    with tarfile.open(tar_path, "w:gz") as tf:
        for fp in files_to_pack:
            arcname = str(fp.relative_to(ROOT))
            tf.add(fp, arcname=f"{bundle_name}/{arcname}")

    tar_sha = compute_sha256(tar_path)
    tar_size_kb = tar_path.stat().st_size / 1024

    print("=" * 70)
    print("PLANT MITOCARTA ZENODO RELEASE ARCHIVE GENERATED")
    print("=" * 70)
    print(f"Version:      {version}")
    print(f"Files packed: {len(files_to_pack)}")
    print(f"ZIP Bundle:   {zip_path} ({zip_size_kb:.1f} KB)")
    print(f"  SHA-256:    {zip_sha}")
    print(f"TAR.GZ:       {tar_path} ({tar_size_kb:.1f} KB)")
    print(f"  SHA-256:    {tar_sha}")
    print("=" * 70)

    # Write bundle manifest
    info = {
        "version": version,
        "bundle_name": bundle_name,
        "files_count": len(files_to_pack),
        "zip": {
            "filename": zip_path.name,
            "bytes": zip_path.stat().st_size,
            "sha256": zip_sha,
        },
        "tar": {
            "filename": tar_path.name,
            "bytes": tar_path.stat().st_size,
            "sha256": tar_sha,
        },
    }
    with open(DIST_DIR / f"{bundle_name}_manifest.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)


if __name__ == "__main__":
    main()
