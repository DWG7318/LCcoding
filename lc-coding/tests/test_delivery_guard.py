from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[2]
guidance = (root / "lc-coding/references/delivery-governance.md").read_text(
    encoding="utf-8"
)
for marker in [
    "Source clauses: [LC-DELIVERY-001]",
    "current Post-Security acceptance",
    "Delivery Method Q&A",
    "DELIVERY_READY",
    "Q&A is not actual Delivery",
    "approved product and customer assets",
    "default internal exclusions",
    "Source code requires explicit Owner authorization",
    "Owner Policy hard constraints",
    "Ubuntu and no-source are recommendations",
    "must not be invented from silence",
    "package evidence and guard",
    "current candidate",
    "does not repeat unchanged product verification",
]:
    assert marker in guidance, marker
guard = root / "lc-coding/scripts/delivery_guard.py"
qa_test = root / "lc-coding/tests/test_delivery_qa.py"
spec = importlib.util.spec_from_file_location("delivery_qa_fixture", qa_test)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
guard_spec = importlib.util.spec_from_file_location("delivery_guard_helpers", guard)
guard_module = importlib.util.module_from_spec(guard_spec)
guard_spec.loader.exec_module(guard_module)
PACKAGE_PATH = "client.zip"
PACKAGE_BYTES = b"current-delivery-package-bytes\n"
REQUIRED_PACKAGE_SUFFIXES = (
    ".whl", ".nupkg", ".deb", ".rpm", ".pkg", ".dmg", ".appx", ".msix",
    ".a", ".lib", ".wasm", ".zip", ".tar.gz", ".exe", ".msi", ".dll",
    ".so", ".dylib", ".jar", ".pdb",
)


def package_digest(data=PACKAGE_BYTES):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verification_receipt(
    receipt_id="VR-1",
    candidate_id=fixtures.CANDIDATE_ID,
    candidate_hash=fixtures.CANDIDATE_HASH,
    asset=PACKAGE_PATH,
    digest=None,
):
    return (
        f"{receipt_id} | {candidate_id} / {candidate_hash} | "
        f"{asset} | {digest or package_digest()}"
    )


def good_manifest(candidate_id=fixtures.CANDIDATE_ID, candidate_hash=fixtures.CANDIDATE_HASH):
    return {
        "delivery_id": "D-1",
        "project_id": "PROJECT-1",
        "product_version": "1.0.0",
        "candidate_id": f"{candidate_id} / {candidate_hash}",
        "included": ["frontend", "client-runtime"],
        "excluded": list(fixtures.LOCKED_EXCLUSIONS),
        "internal_dependencies": [],
        "runtime_certification": "ubuntu-24.04",
        "license_policy": "customer-license",
        "package_hashes": {PACKAGE_PATH: package_digest()},
        "verification_receipts": [verification_receipt(
            candidate_id=candidate_id, candidate_hash=candidate_hash
        )],
        "owner_approval": "APPROVED",
        "delivery_decision_id": "DD-1",
        "delivery_method_confirmed": True,
        "qa_status": "COMPLETE",
    }


def run_guard(path):
    return subprocess.run(
        [sys.executable, str(guard), str(path)], capture_output=True, text=True
    )


def write_manifest(lc, manifest):
    path = lc / "DELIVERY-MANIFEST.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def assert_fails(path):
    project = Path(path).parent.parent
    before = fixtures.snapshot(project)
    result = run_guard(path)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Traceback" not in result.stdout + result.stderr, result.stdout + result.stderr
    assert fixtures.snapshot(project) == before
    return result


with tempfile.TemporaryDirectory(prefix="lccoding-delivery-guard-270-") as td:
    base = Path(td)
    project = base / "fresh"
    lc, decision, status = fixtures.build_delivery_project(project)
    (project / PACKAGE_PATH).write_bytes(PACKAGE_BYTES)
    path = write_manifest(lc, good_manifest())
    before = fixtures.snapshot(project)
    result = run_guard(path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert fixtures.snapshot(project) == before

    def case(name):
        target = base / name
        shutil.copytree(project, target)
        return target / ".lccoding"

    for name, mutate in (
        ("wrong-candidate-hash", lambda item: item.__setitem__(
            "candidate_id", f"{fixtures.CANDIDATE_ID} / {fixtures.NEXT_HASH}"
        )),
        ("wrong-decision", lambda item: item.__setitem__("delivery_decision_id", "DD-OTHER")),
        ("empty-hashes", lambda item: item.__setitem__("package_hashes", {})),
        ("bad-hash", lambda item: item.__setitem__(
            "package_hashes", {"LCCoding-client.zip": "sha256:" + "C" * 64}
        )),
        ("unsafe-hash-path", lambda item: item.__setitem__(
            "package_hashes", {"../escape.zip": "sha256:" + "c" * 64}
        )),
        ("ads-hash-path", lambda item: item.__setitem__(
            "package_hashes", {"client.zip:secret": package_digest()}
        )),
        ("backslash-hash-path", lambda item: item.__setitem__(
            "package_hashes", {"bundle\\client.zip": package_digest()}
        )),
        ("reserved-hash-path", lambda item: item.__setitem__(
            "package_hashes", {"NUL.zip": package_digest()}
        )),
        ("bidi-hash-path", lambda item: item.__setitem__(
            "package_hashes", {"client\u202ezip": package_digest()}
        )),
        ("trailing-dot-hash-path", lambda item: item.__setitem__(
            "package_hashes", {"bundle./client.zip": package_digest()}
        )),
        ("hashes-list", lambda item: item.__setitem__("package_hashes", [])),
        ("forbidden-asset", lambda item: item["included"].append("LCapi")),
        ("forbidden-casefold", lambda item: item["included"].append("lcapi")),
        ("forbidden-nested", lambda item: item["included"].append("bundle/LCapi/source")),
        ("forbidden-versioned", lambda item: item["included"].append(
            "bundle/LCapi-2.7.0.zip"
        )),
        ("forbidden-versioned-underscore", lambda item: item["included"].append(
            "LCCoding_v2.7.0.zip"
        )),
        ("forbidden-versioned-at", lambda item: item["included"].append(
            "Calabash@2.5.0.tar.gz"
        )),
        ("forbidden-wheel", lambda item: item["included"].append(
            "bundle/LCapi-2.7.0.whl"
        )),
        ("forbidden-nupkg", lambda item: item["included"].append(
            "bundle/LCapi-2.7.0.nupkg"
        )),
        ("forbidden-dot-version", lambda item: item["included"].append(
            "bundle/LCapi.2.7.0.whl"
        )),
        ("forbidden-versioned-other", lambda item: item["included"].append(
            "bundle/Project Intelligence_v1.2.3.zip"
        )),
        ("forbidden-basename", lambda item: item["included"].append("LCapi.zip")),
        ("forbidden-library-basename", lambda item: item["included"].append("LCapi.dll")),
        ("forbidden-trailing-dot", lambda item: item["included"].append("LCapi.")),
        ("forbidden-ads", lambda item: item["included"].append("LCapi:stream")),
        ("casefold-conflict", lambda item: (
            item["included"].append("Frontend"), item["excluded"].append("frontend")
        )),
        ("missing-locked-exclusion", lambda item: item["excluded"].pop()),
        ("qa-incomplete", lambda item: item.__setitem__("qa_status", "PENDING")),
        ("owner-missing", lambda item: item.__setitem__("owner_approval", "PENDING")),
        ("runtime-missing", lambda item: item.__setitem__("runtime_certification", "")),
        ("runtime-pending", lambda item: item.__setitem__("runtime_certification", "PENDING")),
        ("license-missing", lambda item: item.__setitem__("license_policy", "")),
        ("license-pending", lambda item: item.__setitem__("license_policy", "PENDING")),
        ("project-id-pending", lambda item: item.__setitem__("project_id", "PENDING")),
        ("project-id-pass", lambda item: item.__setitem__("project_id", "PASS")),
        ("project-id-invalid", lambda item: item.__setitem__("project_id", "INVALID")),
        ("project-id-rejected", lambda item: item.__setitem__("project_id", "REJECTED")),
        ("project-id-fake", lambda item: item.__setitem__("project_id", "FAKE")),
        ("project-id-test", lambda item: item.__setitem__("project_id", "TEST")),
        ("project-id-mock", lambda item: item.__setitem__("project_id", "MOCK")),
        ("project-id-stub", lambda item: item.__setitem__("project_id", "STUB")),
        ("project-id-pass-prefixed", lambda item: item.__setitem__(
            "project_id", "PASS-1"
        )),
        ("project-id-invalid-prefixed", lambda item: item.__setitem__(
            "project_id", "INVALID-1"
        )),
        ("project-id-approved-prefixed", lambda item: item.__setitem__(
            "project_id", "APPROVED-1"
        )),
        ("delivery-id-test", lambda item: item.__setitem__("delivery_id", "TEST")),
        ("runtime-invalid", lambda item: item.__setitem__("runtime_certification", "INVALID")),
        ("license-invalid", lambda item: item.__setitem__("license_policy", "INVALID")),
        ("product-version-pending", lambda item: item.__setitem__("product_version", "PENDING")),
        ("product-version-invalid", lambda item: item.__setitem__("product_version", "1.0")),
    ):
        lc_case = case(name)
        manifest = copy.deepcopy(good_manifest())
        mutate(manifest)
        assert_fails(write_manifest(lc_case, manifest))

    duplicate = case("duplicate-package-hashes")
    raw = json.dumps(good_manifest()).replace(
        '"package_hashes":', '"package_hashes":{"shadow":"sha256:' + "d" * 64 + '"},"package_hashes":', 1
    )
    duplicate_path = duplicate / "DELIVERY-MANIFEST.json"
    duplicate_path.write_text(raw, encoding="utf-8")
    assert_fails(duplicate_path)

    manifest_nonfinite = case("manifest-nonfinite")
    raw = json.dumps(good_manifest()).replace(
        '"project_id": "PROJECT-1"', '"project_id": NaN'
    )
    manifest_nonfinite_path = manifest_nonfinite / "DELIVERY-MANIFEST.json"
    manifest_nonfinite_path.write_text(raw, encoding="utf-8")
    assert_fails(manifest_nonfinite_path)

    missing_package = case("missing-package")
    (missing_package.parent / PACKAGE_PATH).unlink()
    assert_fails(missing_package / "DELIVERY-MANIFEST.json")

    changed_package = case("changed-package")
    (changed_package.parent / PACKAGE_PATH).write_bytes(b"changed after manifest\n")
    assert_fails(changed_package / "DELIVERY-MANIFEST.json")

    receipt_mutations = {
        "receipt-wrong-candidate": [verification_receipt(candidate_id=fixtures.NEXT_ID)],
        "receipt-wrong-candidate-hash": [verification_receipt(candidate_hash=fixtures.NEXT_HASH)],
        "receipt-wrong-path": [verification_receipt(asset="other.zip")],
        "receipt-wrong-digest": [verification_receipt(digest="sha256:" + "d" * 64)],
        "receipt-duplicate": [verification_receipt(), verification_receipt()],
        "receipt-missing": [],
        "receipt-extra": [verification_receipt(), verification_receipt(
            receipt_id="VR-EXTRA", asset="other.zip"
        )],
        "receipt-generic": [verification_receipt(receipt_id="PENDING")],
        "receipt-old-fake": ["FAKE"],
        "receipt-shaped-fake": [verification_receipt(receipt_id="FAKE")],
        "receipt-pass": [verification_receipt(receipt_id="PASS")],
        "receipt-ready": [verification_receipt(receipt_id="READY")],
        "receipt-complete": [verification_receipt(receipt_id="COMPLETE")],
        "receipt-invalid": [verification_receipt(receipt_id="INVALID")],
        "receipt-approved": [verification_receipt(receipt_id="APPROVED")],
        "receipt-rejected": [verification_receipt(receipt_id="REJECTED")],
        "receipt-test": [verification_receipt(receipt_id="TEST")],
        "receipt-mock": [verification_receipt(receipt_id="MOCK")],
        "receipt-stub": [verification_receipt(receipt_id="STUB")],
        "receipt-pass-prefixed": [verification_receipt(receipt_id="PASS-1")],
        "receipt-invalid-prefixed": [verification_receipt(receipt_id="INVALID-1")],
        "receipt-approved-prefixed": [verification_receipt(receipt_id="APPROVED-1")],
        "receipt-multitoken-status-prefixed": [verification_receipt(
            receipt_id="POST_SECURITY_OWNER_ACCEPTED-1"
        )],
    }
    for name, receipts in receipt_mutations.items():
        receipt_case = case(name)
        manifest = good_manifest()
        manifest["verification_receipts"] = receipts
        assert_fails(write_manifest(receipt_case, manifest))

    duplicate_receipt_id = case("duplicate-receipt-id")
    (duplicate_receipt_id.parent / "other.zip").write_bytes(b"other\n")
    other_digest = package_digest(b"other\n")
    manifest = good_manifest()
    manifest["package_hashes"]["other.zip"] = other_digest
    manifest["verification_receipts"].append(
        verification_receipt(asset="other.zip", digest=other_digest)
    )
    assert_fails(write_manifest(duplicate_receipt_id, manifest))

    def internal_package_case(name, asset):
        lc_case = case(name)
        target = lc_case.parent.joinpath(*asset.split("/"))
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(PACKAGE_BYTES)
        digest = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
        manifest = good_manifest()
        manifest["package_hashes"] = {asset: digest}
        manifest["verification_receipts"] = [verification_receipt(
            asset=asset, digest=digest
        )]
        assert_fails(write_manifest(lc_case, manifest))

    internal_package_case("status-as-package", ".lccoding/status.json")
    internal_package_case(
        "closure-as-package", ".lccoding/VULNERABILITY-CLOSURE.json"
    )
    internal_package_case(
        "casefold-internal-package", ".LCCODING/status-copy.json"
    )
    internal_package_case("git-metadata-as-package", ".git/objects/fake.pack")
    internal_package_case(
        "protected-package-basename", "bundle/LCapi-2.7.0.zip"
    )
    for index, suffix in enumerate(REQUIRED_PACKAGE_SUFFIXES):
        internal_package_case(
            "protected-package-suffix-" + str(index),
            "bundle/LCapi-2.7.0" + suffix,
        )
        assert guard_module.protected_asset(
            "LCapi-2.7.0" + suffix, fixtures.LOCKED_EXCLUSIONS
        )
    internal_package_case(
        "protected-package-dot-version", "bundle/LCapi.2.7.0.whl"
    )
    for index, asset in enumerate((
        "LCapi-2.7.0.zip.exe",
        "LCapi-2.7.0.whl.gz",
    )):
        assert guard_module.protected_asset(asset, fixtures.LOCKED_EXCLUSIONS)
        internal_package_case(
            "protected-compound-wrapper-" + str(index), "bundle/" + asset
        )

    legal_versioned = case("legal-client-versioned-package")
    legal_asset = "client-2.7.0.whl"
    (legal_versioned.parent / legal_asset).write_bytes(PACKAGE_BYTES)
    manifest = good_manifest()
    manifest["package_hashes"] = {legal_asset: package_digest()}
    manifest["verification_receipts"] = [verification_receipt(asset=legal_asset)]
    legal_result = run_guard(write_manifest(legal_versioned, manifest))
    assert legal_result.returncode == 0, legal_result.stdout + legal_result.stderr
    for index, legal_asset in enumerate((
        "client-2.7.0.zip.exe",
        "client-2.7.0.whl.gz",
    )):
        legal_compound = case("legal-client-compound-" + str(index))
        (legal_compound.parent / legal_asset).write_bytes(PACKAGE_BYTES)
        manifest = good_manifest()
        manifest["package_hashes"] = {legal_asset: package_digest()}
        manifest["verification_receipts"] = [verification_receipt(
            asset=legal_asset
        )]
        legal_compound_result = run_guard(
            write_manifest(legal_compound, manifest)
        )
        assert legal_compound_result.returncode == 0, (
            legal_compound_result.stdout + legal_compound_result.stderr
        )

    disguised_hardlink = case("single-hidden-hardlink-package")
    disguised_path = disguised_hardlink.parent / PACKAGE_PATH
    disguised_path.unlink()
    os.link(disguised_hardlink / "status.json", disguised_path)
    disguised_digest = "sha256:" + hashlib.sha256(
        disguised_path.read_bytes()
    ).hexdigest()
    manifest = good_manifest()
    manifest["package_hashes"] = {PACKAGE_PATH: disguised_digest}
    manifest["verification_receipts"] = [verification_receipt(
        asset=PACKAGE_PATH, digest=disguised_digest
    )]
    assert disguised_path.stat().st_nlink > 1
    assert_fails(write_manifest(disguised_hardlink, manifest))

    case_alias = case("case-only-package-alias")
    manifest = good_manifest()
    manifest["package_hashes"]["CLIENT.ZIP"] = package_digest()
    manifest["verification_receipts"].append(
        verification_receipt(receipt_id="VR-CASE", asset="CLIENT.ZIP")
    )
    alias_result = assert_fails(write_manifest(case_alias, manifest))
    assert "Windows identity" in alias_result.stdout
    assert guard_module.windows_package_identity("client.zip") == (
        guard_module.windows_package_identity("CLIENT.ZIP")
    )

    unicode_alias = case("unicode-package-alias")
    composed = "caf\u00e9.zip"
    decomposed = "cafe\u0301.zip"
    (unicode_alias.parent / composed).write_bytes(PACKAGE_BYTES)
    manifest = good_manifest()
    manifest["package_hashes"] = {decomposed: package_digest()}
    manifest["verification_receipts"] = [verification_receipt(
        asset=decomposed
    )]
    assert_fails(write_manifest(unicode_alias, manifest))

    hardlink_alias = case("hardlink-package-alias")
    alias_path = hardlink_alias.parent / "alias.zip"
    try:
        os.link(hardlink_alias.parent / PACKAGE_PATH, alias_path)
    except OSError:
        pass
    else:
        manifest = good_manifest()
        manifest["package_hashes"]["alias.zip"] = package_digest()
        manifest["verification_receipts"].append(
            verification_receipt(receipt_id="VR-ALIAS", asset="alias.zip")
        )
        hardlink_result = assert_fails(write_manifest(hardlink_alias, manifest))
        assert "physical file" in hardlink_result.stdout

    multi_package = case("multi-package-valid")
    (multi_package.parent / "second.zip").write_bytes(b"second\n")
    second_digest = package_digest(b"second\n")
    manifest = good_manifest()
    manifest["package_hashes"]["second.zip"] = second_digest
    manifest["verification_receipts"].append(
        verification_receipt(
            receipt_id="VR-2", asset="second.zip", digest=second_digest
        )
    )
    multi_result = run_guard(write_manifest(multi_package, manifest))
    assert multi_result.returncode == 0, multi_result.stdout + multi_result.stderr

    symlink_case = case("symlink-package")
    outside = base / "outside.zip"
    outside.write_bytes(PACKAGE_BYTES)
    link = symlink_case.parent / "linked.zip"
    try:
        link.symlink_to(outside)
    except OSError:
        resolved, path_error = guard_module.resolve_package_path(
            symlink_case.parent, "../outside.zip"
        )
        assert resolved is None and path_error
    else:
        manifest = good_manifest()
        manifest["package_hashes"] = {"linked.zip": package_digest()}
        manifest["verification_receipts"] = [verification_receipt(asset="linked.zip")]
        assert_fails(write_manifest(symlink_case, manifest))

    invalid_gate = case("invalid-gate")
    invalid_status = json.loads((invalid_gate / "status.json").read_text())
    invalid_status["phase_gates"]["DELIVERY_READY"] = "INVALID"
    (invalid_gate / "status.json").write_text(json.dumps(invalid_status))
    assert_fails(invalid_gate / "DELIVERY-MANIFEST.json")

    missing_decision = case("missing-decision")
    (missing_decision / "DELIVERY-DECISION.json").unlink()
    assert_fails(missing_decision / "DELIVERY-MANIFEST.json")

    neutral = base / "neutral"
    neutral_lc, _, _ = fixtures.build_delivery_project(neutral, preservation="NEUTRAL")
    (neutral / PACKAGE_PATH).write_bytes(PACKAGE_BYTES)
    neutral_manifest = write_manifest(neutral_lc, good_manifest())
    neutral_result = run_guard(neutral_manifest)
    assert neutral_result.returncode == 0, neutral_result.stdout + neutral_result.stderr

    packaging = base / "packaging"
    packaging_lc, _, _ = fixtures.build_delivery_project(
        packaging,
        status_id=fixtures.NEXT_ID,
        status_hash=fixtures.NEXT_HASH,
        receipt_id=fixtures.CANDIDATE_ID,
        receipt_hash=fixtures.CANDIDATE_HASH,
        preservation="PACKAGING",
    )
    (packaging / PACKAGE_PATH).write_bytes(PACKAGE_BYTES)
    packaging_manifest = write_manifest(
        packaging_lc, good_manifest(fixtures.NEXT_ID, fixtures.NEXT_HASH)
    )
    packaging_result = run_guard(packaging_manifest)
    assert packaging_result.returncode == 0, (
        packaging_result.stdout + packaging_result.stderr
    )

print("PASS: delivery guard joins current decision, security and package hashes")
