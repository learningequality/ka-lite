set "BIN_DIR=%~dp0"
setx PATH "%path%;%BIN_DIR%;"
reg add "HKEY_CURRENT_USER\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /f /d "%path%"
