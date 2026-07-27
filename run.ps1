Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
uv run python main.py
