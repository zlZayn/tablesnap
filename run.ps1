Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "正在启动..."
uv run python main.py
