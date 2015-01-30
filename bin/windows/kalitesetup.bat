set "BIN_DIR=%~dp0"
set path=%path%;%BIN_DIR%
reg add "HKEY_CURRENT_USER\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /f /d %path%