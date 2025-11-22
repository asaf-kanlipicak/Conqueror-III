; Custom NSIS installer script for Conqueror III Client
; This file is included by electron-builder's default NSIS script

; Macro called after installation is complete
!macro customInstall
  ; Add any custom post-install logic here if needed
  ; For now, NSIS handles shortcuts and registry automatically
!macroend

; Macro called before uninstallation
!macro customUnInstall
  ; Add any custom pre-uninstall logic here if needed
  ; For now, NSIS handles cleanup automatically
!macroend
