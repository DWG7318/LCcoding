from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "lc-coding/bi/src-tauri/windows/hooks.nsh"

text = HOOKS.read_text(encoding="utf-8")

required_markers = (
    '!define LCCODING_PATH_STATE_KEY "Software\\lccoding\\LCCoding BI"',
    "!macro LCCodingDefineUserPathValueExists UNPREFIX",
    'EnumRegValue $R7 HKCU "Environment" $R8',
    '!insertmacro LCCodingDefineUserPathValueExists ""',
    '!insertmacro LCCodingDefineUserPathValueExists "un."',
    "LCCodingPathReadFailure:",
    "LCCodingPathUnreadable:",
    "un.LCCodingPathReadFailure:",
    "un.LCCodingPathUnreadable:",
    'Abort "LCCODING_PATH_INSTALL_READ_FAILED"',
    'Abort "LCCODING_PATH_UNINSTALL_READ_FAILED"',
    "LCCodingPathCapacityExceeded:",
    'Abort "LCCODING_PATH_INSTALL_CAPACITY_FAILED"',
    'ReadRegDWORD $R2 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive"',
    'WriteRegDWORD HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreExists"',
    'WriteRegExpandStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreRaw"',
    'WriteRegExpandStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPostRaw"',
    'WriteRegStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnInstallRoot"',
    'WriteRegDWORD HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive" 1',
    "LCCodingPathSnapshot:",
    "LCCodingPathStatePreserve:",
    "Function un.LCCodingRemoveExactInstallRootToken",
    "un.LCCodingPathRestoreExact:",
    "un.LCCodingPathRemoveCurrentOnly:",
    "un.LCCodingPathTransactionCleanup:",
    'WriteRegExpandStr HKCU "Environment" "Path" "$R7"',
    'DeleteRegValue HKCU "Environment" "Path"',
    'SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE}',
)
for marker in required_markers:
    assert marker in text, marker

for forbidden in (
    "${UnStrTok}",
    "LCCodingRemoveUserPathLoop",
    'StrCpy $R3 "$R3;$R2"',
    "HKLM",
    "allUsers",
    "NSIS_MAX_STRLEN",
    "reg.exe",
    "powershell",
    "Registry::",
    "nsExec::",
    "ExecWait",
):
    assert forbidden.lower() not in text.lower(), forbidden

transaction_values = (
    "PathTxnActive",
    "PathTxnVersion",
    "PathTxnPreExists",
    "PathTxnPreRaw",
    "PathTxnPostRaw",
    "PathTxnInstallRoot",
)
for value in transaction_values:
    assert text.count(f'DeleteRegValue HKCU "${{LCCODING_PATH_STATE_KEY}}" "{value}"') == 1

snapshot = text.index("LCCodingPathSnapshot:")
path_write = text.index('WriteRegExpandStr HKCU "Environment" "Path"')
post_write = text.index(
    'WriteRegExpandStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPostRaw"'
)
active_write = text.index(
    'WriteRegDWORD HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive" 1'
)
assert snapshot < path_write < post_write < active_write

exact_restore = text.index("un.LCCodingPathRestoreExact:")
safe_fallback = text.index("un.LCCodingPathRemoveCurrentOnly:")
cleanup = text.index("un.LCCodingPathTransactionCleanup:")
assert exact_restore < safe_fallback < cleanup
exact_post_image_compare = (
    'StrCmpS $R0 "$R5" '
    "un.LCCodingPathRestoreExact un.LCCodingPathRemoveCurrentOnly"
)
case_insensitive_post_image_compare = (
    'StrCmp $R0 "$R5" '
    "un.LCCodingPathRestoreExact un.LCCodingPathRemoveCurrentOnly"
)
assert exact_post_image_compare in text
assert case_insensitive_post_image_compare not in text
assert 'StrCmp $R6 0 0 +3' in text

install_read = text.index('ReadRegStr $R0 HKCU "Environment" "Path"')
install_classify = text.index(
    "IfErrors LCCodingPathReadFailure LCCodingPathPresent", install_read
)
install_failure = text.index("LCCodingPathReadFailure:", install_classify)
install_enum = text.index("Call LCCodingUserPathValueExists", install_failure)
install_dispatch = text.index(
    "StrCmp $R9 0 LCCodingPathMissing LCCodingPathUnreadable", install_enum
)
install_unreadable = text.index("LCCodingPathUnreadable:", install_dispatch)
install_errorlevel = text.index("SetErrorLevel 65", install_unreadable)
install_abort = text.index(
    'Abort "LCCODING_PATH_INSTALL_READ_FAILED"', install_errorlevel
)
assert (
    install_read
    < install_classify
    < install_failure
    < install_enum
    < install_dispatch
    < install_unreadable
    < install_errorlevel
    < install_abort
    < snapshot
    < path_write
)

uninstall_read = text.index(
    'ReadRegStr $R0 HKCU "Environment" "Path"', install_read + 1
)
uninstall_classify = text.index(
    "IfErrors un.LCCodingPathReadFailure un.LCCodingPathPresent", uninstall_read
)
uninstall_failure = text.index("un.LCCodingPathReadFailure:", uninstall_classify)
uninstall_enum = text.index(
    "Call un.LCCodingUserPathValueExists", uninstall_failure
)
uninstall_dispatch = text.index(
    "StrCmp $R9 0 un.LCCodingPathMissing un.LCCodingPathUnreadable",
    uninstall_enum,
)
uninstall_unreadable = text.index(
    "un.LCCodingPathUnreadable:", uninstall_dispatch
)
uninstall_errorlevel = text.index("SetErrorLevel 66", uninstall_unreadable)
uninstall_abort = text.index(
    'Abort "LCCODING_PATH_UNINSTALL_READ_FAILED"', uninstall_errorlevel
)
assert (
    uninstall_read
    < uninstall_classify
    < uninstall_failure
    < uninstall_enum
    < uninstall_dispatch
    < uninstall_unreadable
    < uninstall_errorlevel
    < uninstall_abort
    < cleanup
)

append = text.index("LCCodingPathAppend:")
capacity_compare = text.index(
    "IntCmp $R5 1023 LCCodingPathCapacitySafe LCCodingPathCapacitySafe LCCodingPathCapacityExceeded",
    append,
)
capacity_exceeded = text.index("LCCodingPathCapacityExceeded:", capacity_compare)
capacity_errorlevel = text.index("SetErrorLevel 67", capacity_exceeded)
capacity_abort = text.index(
    'Abort "LCCODING_PATH_INSTALL_CAPACITY_FAILED"', capacity_errorlevel
)
capacity_safe = text.index("LCCodingPathCapacitySafe:", capacity_abort)
append_value = text.index('StrCpy $R0 "$R0;$INSTDIR"', capacity_safe)
assert (
    append
    < capacity_compare
    < capacity_exceeded
    < capacity_errorlevel
    < capacity_abort
    < capacity_safe
    < append_value
    < path_write
)

assert text.count('EnumRegValue $R7 HKCU "Environment" $R8') == 1

# This static contract requires long or otherwise unreadable existing PATH values to
# fail closed; it does not pretend to execute an over-NSIS_MAX_STRLEN registry value.
# Real registry roundtrip remains a later independent Windows acceptance.
print("PASS: NSIS PATH transaction and concurrent-change contract")
