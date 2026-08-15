!include "LogicLib.nsh"
!include "WinMessages.nsh"

!define LCCODING_PATH_STATE_KEY "Software\lccoding\LCCoding BI"

!macro LCCodingDefineUserPathValueExists UNPREFIX
Function ${UNPREFIX}LCCodingUserPathValueExists
  StrCpy $R8 0
  StrCpy $R9 0

  ${UNPREFIX}LCCodingUserPathValueExistsLoop:
    ClearErrors
    EnumRegValue $R7 HKCU "Environment" $R8
    IfErrors ${UNPREFIX}LCCodingUserPathValueExistsDone 0
    StrCmp $R7 "Path" ${UNPREFIX}LCCodingUserPathValueExistsFound 0
    IntOp $R8 $R8 + 1
    Goto ${UNPREFIX}LCCodingUserPathValueExistsLoop

  ${UNPREFIX}LCCodingUserPathValueExistsFound:
    StrCpy $R9 1

  ${UNPREFIX}LCCodingUserPathValueExistsDone:
FunctionEnd
!macroend

!insertmacro LCCodingDefineUserPathValueExists ""
!insertmacro LCCodingDefineUserPathValueExists "un."

Function LCCodingAddUserPath
  ClearErrors
  ReadRegStr $R0 HKCU "Environment" "Path"
  IfErrors LCCodingPathReadFailure LCCodingPathPresent

  LCCodingPathReadFailure:
    Call LCCodingUserPathValueExists
    StrCmp $R9 0 LCCodingPathMissing LCCodingPathUnreadable

  LCCodingPathUnreadable:
    SetErrorLevel 65
    Abort "LCCODING_PATH_INSTALL_READ_FAILED"

  LCCodingPathMissing:
    StrCpy $R0 ""
    StrCpy $R1 0
    Goto LCCodingPathState

  LCCodingPathPresent:
    StrCpy $R1 1

  LCCodingPathState:
    ClearErrors
    ReadRegDWORD $R2 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive"
    IfErrors LCCodingPathSnapshot 0
    StrCmp $R2 1 LCCodingPathStatePreserve LCCodingPathSnapshot

  LCCodingPathSnapshot:
    WriteRegStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnVersion" "1"
    WriteRegDWORD HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreExists" $R1
    StrCmp $R1 1 0 +2
      WriteRegExpandStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreRaw" "$R0"
    WriteRegStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnInstallRoot" "$INSTDIR"
    StrCpy $R9 1
    Goto LCCodingPathFindToken

  LCCodingPathStatePreserve:
    StrCpy $R9 0

  LCCodingPathFindToken:
    StrCpy $R3 0
    StrLen $R4 $R0

  LCCodingPathFindTokenLoop:
    StrCpy $R5 $R3

  LCCodingPathFindTokenEnd:
    IntCmp $R5 $R4 LCCodingPathTokenReady LCCodingPathFindTokenChar LCCodingPathTokenReady

  LCCodingPathFindTokenChar:
    StrCpy $R6 $R0 1 $R5
    StrCmp $R6 ";" LCCodingPathTokenReady
    IntOp $R5 $R5 + 1
    Goto LCCodingPathFindTokenEnd

  LCCodingPathTokenReady:
    IntOp $R6 $R5 - $R3
    StrCpy $R7 $R0 $R6 $R3
    StrCmp $R7 "$INSTDIR" LCCodingPathPostReady
    IntCmp $R5 $R4 LCCodingPathAppend LCCodingPathNextToken LCCodingPathAppend

  LCCodingPathNextToken:
    IntOp $R3 $R5 + 1
    Goto LCCodingPathFindTokenLoop

  LCCodingPathAppend:
    StrLen $R3 $R0
    StrLen $R4 $INSTDIR
    IntOp $R5 $R3 + $R4
    StrCmp $R0 "" LCCodingPathCapacityCompare 0
    IntOp $R5 $R5 + 1

  LCCodingPathCapacityCompare:
    IntCmp $R5 1023 LCCodingPathCapacitySafe LCCodingPathCapacitySafe LCCodingPathCapacityExceeded

  LCCodingPathCapacityExceeded:
    SetErrorLevel 67
    Abort "LCCODING_PATH_INSTALL_CAPACITY_FAILED"

  LCCodingPathCapacitySafe:
    StrCmp $R0 "" 0 +3
      StrCpy $R0 "$INSTDIR"
      Goto LCCodingPathWrite
    StrCpy $R0 "$R0;$INSTDIR"

  LCCodingPathWrite:
    WriteRegExpandStr HKCU "Environment" "Path" "$R0"

  LCCodingPathPostReady:
    StrCmp $R9 1 0 LCCodingPathBroadcast
    WriteRegExpandStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPostRaw" "$R0"
    WriteRegDWORD HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive" 1

  LCCodingPathBroadcast:
    SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE} 0 "STR:Environment" /TIMEOUT=5000
FunctionEnd

Function un.LCCodingRemoveExactInstallRootToken
  StrCpy $R9 0
  StrCpy $R1 0

  un.LCCodingExactTokenLoop:
    StrLen $R2 $R0
    IntCmp $R1 $R2 un.LCCodingExactTokenDone un.LCCodingExactTokenScan un.LCCodingExactTokenDone

  un.LCCodingExactTokenScan:
    StrCpy $R3 $R1

  un.LCCodingExactTokenFindEnd:
    IntCmp $R3 $R2 un.LCCodingExactTokenReady un.LCCodingExactTokenChar un.LCCodingExactTokenReady

  un.LCCodingExactTokenChar:
    StrCpy $R4 $R0 1 $R3
    StrCmp $R4 ";" un.LCCodingExactTokenReady
    IntOp $R3 $R3 + 1
    Goto un.LCCodingExactTokenFindEnd

  un.LCCodingExactTokenReady:
    IntOp $R4 $R3 - $R1
    StrCpy $R5 $R0 $R4 $R1
    StrCmp $R5 "$INSTDIR" un.LCCodingExactTokenRemove
    IntCmp $R3 $R2 un.LCCodingExactTokenDone un.LCCodingExactTokenNext un.LCCodingExactTokenDone

  un.LCCodingExactTokenNext:
    IntOp $R1 $R3 + 1
    Goto un.LCCodingExactTokenLoop

  un.LCCodingExactTokenRemove:
    StrCmp $R1 0 un.LCCodingExactTokenRemoveFirst un.LCCodingExactTokenRemoveLater

  un.LCCodingExactTokenRemoveFirst:
    IntCmp $R3 $R2 un.LCCodingExactTokenRemoveOnly un.LCCodingExactTokenRemoveFirstDelimited un.LCCodingExactTokenRemoveOnly

  un.LCCodingExactTokenRemoveFirstDelimited:
    IntOp $R6 $R3 + 1
    StrCpy $R0 $R0 "" $R6
    StrCpy $R9 1
    StrCpy $R1 0
    Goto un.LCCodingExactTokenLoop

  un.LCCodingExactTokenRemoveOnly:
    StrCpy $R0 ""
    StrCpy $R9 1
    Goto un.LCCodingExactTokenDone

  un.LCCodingExactTokenRemoveLater:
    IntOp $R6 $R1 - 1
    StrCpy $R7 $R0 $R6
    StrCpy $R8 $R0 "" $R3
    StrCpy $R0 "$R7$R8"
    StrCpy $R9 1
    StrCpy $R1 0
    Goto un.LCCodingExactTokenLoop

  un.LCCodingExactTokenDone:
FunctionEnd

Function un.LCCodingRemoveUserPath
  ClearErrors
  ReadRegStr $R0 HKCU "Environment" "Path"
  IfErrors un.LCCodingPathReadFailure un.LCCodingPathPresent

  un.LCCodingPathReadFailure:
    Call un.LCCodingUserPathValueExists
    StrCmp $R9 0 un.LCCodingPathMissing un.LCCodingPathUnreadable

  un.LCCodingPathUnreadable:
    SetErrorLevel 66
    Abort "LCCODING_PATH_UNINSTALL_READ_FAILED"

  un.LCCodingPathMissing:
    StrCpy $R0 ""
    StrCpy $R1 0
    Goto un.LCCodingPathReadTransaction

  un.LCCodingPathPresent:
    StrCpy $R1 1

  un.LCCodingPathReadTransaction:
    ClearErrors
    ReadRegDWORD $R2 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive"
    IfErrors un.LCCodingPathRemoveCurrentOnly 0
    StrCmp $R2 1 0 un.LCCodingPathRemoveCurrentOnly
    ClearErrors
    ReadRegStr $R3 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnVersion"
    IfErrors un.LCCodingPathRemoveCurrentOnly 0
    StrCmp $R3 "1" 0 un.LCCodingPathRemoveCurrentOnly
    ClearErrors
    ReadRegStr $R4 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnInstallRoot"
    IfErrors un.LCCodingPathRemoveCurrentOnly 0
    StrCmp $R4 "$INSTDIR" 0 un.LCCodingPathRemoveCurrentOnly
    ClearErrors
    ReadRegStr $R5 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPostRaw"
    IfErrors un.LCCodingPathRemoveCurrentOnly 0
    ClearErrors
    ReadRegDWORD $R6 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreExists"
    IfErrors un.LCCodingPathRemoveCurrentOnly 0
    StrCmp $R6 0 un.LCCodingPathTransactionReady 0
    StrCmp $R6 1 0 un.LCCodingPathRemoveCurrentOnly
    ClearErrors
    ReadRegStr $R7 HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreRaw"
    IfErrors un.LCCodingPathRemoveCurrentOnly 0

  un.LCCodingPathTransactionReady:
    StrCmp $R1 1 0 un.LCCodingPathRemoveCurrentOnly
    StrCmpS $R0 "$R5" un.LCCodingPathRestoreExact un.LCCodingPathRemoveCurrentOnly

  un.LCCodingPathRestoreExact:
    StrCmp $R6 0 0 +3
      DeleteRegValue HKCU "Environment" "Path"
      Goto un.LCCodingPathTransactionCleanup
    WriteRegExpandStr HKCU "Environment" "Path" "$R7"
    Goto un.LCCodingPathTransactionCleanup

  un.LCCodingPathRemoveCurrentOnly:
    StrCmp $R1 1 0 un.LCCodingPathTransactionCleanup
    Call un.LCCodingRemoveExactInstallRootToken
    StrCmp $R9 1 0 un.LCCodingPathTransactionCleanup
    StrCmp $R0 "" 0 +3
      DeleteRegValue HKCU "Environment" "Path"
      Goto un.LCCodingPathTransactionCleanup
    WriteRegExpandStr HKCU "Environment" "Path" "$R0"

  un.LCCodingPathTransactionCleanup:
    DeleteRegValue HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive"
    DeleteRegValue HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnVersion"
    DeleteRegValue HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreExists"
    DeleteRegValue HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPreRaw"
    DeleteRegValue HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPostRaw"
    DeleteRegValue HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnInstallRoot"
    SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE} 0 "STR:Environment" /TIMEOUT=5000
FunctionEnd

!macro NSIS_HOOK_POSTINSTALL
  Delete "$INSTDIR\lccoding.exe"
  Call LCCodingAddUserPath
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  Call un.LCCodingRemoveUserPath
!macroend
