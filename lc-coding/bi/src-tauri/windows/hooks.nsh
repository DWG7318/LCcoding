!include "LogicLib.nsh"
!include "StrFunc.nsh"
!include "WinMessages.nsh"

${StrTok}
${UnStrTok}

Function LCCodingAddUserPath
  ReadRegStr $R0 HKCU "Environment" "Path"
  StrCpy $R1 0

  LCCodingAddUserPathLoop:
    ${StrTok} $R2 "$R0" ";" "$R1" "1"
    StrCmp $R2 "" LCCodingAddUserPathAppend
    StrCmp $R2 "$INSTDIR" LCCodingAddUserPathDone
    IntOp $R1 $R1 + 1
    Goto LCCodingAddUserPathLoop

  LCCodingAddUserPathAppend:
    StrCmp $R0 "" 0 +3
      StrCpy $R0 "$INSTDIR"
      Goto LCCodingAddUserPathWrite
    StrCpy $R0 "$R0;$INSTDIR"

  LCCodingAddUserPathWrite:
    WriteRegExpandStr HKCU "Environment" "Path" "$R0"
    SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE} 0 "STR:Environment" /TIMEOUT=5000

  LCCodingAddUserPathDone:
FunctionEnd

Function un.LCCodingRemoveUserPath
  ReadRegStr $R0 HKCU "Environment" "Path"
  StrCpy $R1 0
  StrCpy $R3 ""

  LCCodingRemoveUserPathLoop:
    ${UnStrTok} $R2 "$R0" ";" "$R1" "1"
    StrCmp $R2 "" LCCodingRemoveUserPathWrite
    IntOp $R1 $R1 + 1
    StrCmp $R2 "$INSTDIR" LCCodingRemoveUserPathLoop
    StrCmp $R3 "" 0 +3
      StrCpy $R3 "$R2"
      Goto LCCodingRemoveUserPathLoop
    StrCpy $R3 "$R3;$R2"
    Goto LCCodingRemoveUserPathLoop

  LCCodingRemoveUserPathWrite:
    StrCmp $R3 "" 0 +3
      DeleteRegValue HKCU "Environment" "Path"
      Goto LCCodingRemoveUserPathBroadcast
    WriteRegExpandStr HKCU "Environment" "Path" "$R3"

  LCCodingRemoveUserPathBroadcast:
    SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE} 0 "STR:Environment" /TIMEOUT=5000
FunctionEnd

!macro NSIS_HOOK_POSTINSTALL
  Delete "$INSTDIR\lccoding.exe"
  Call LCCodingAddUserPath
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  Call un.LCCodingRemoveUserPath
!macroend
