Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "正在启动..." -NoNewline
Start-Sleep -Milliseconds 200
Write-Host "`r$(' ' * 14)`r" -NoNewline
uv run python main.py
