"""Centralised prompt templates for VLM-based screenshot -> CSV extraction.

All prompt text lives here so that tweaking the model's behaviour never
requires hunting through client code.
"""

SYSTEM_PROMPT = (
    "You are a precise data-extraction assistant. "
    "Your job is to extract ALL visible tabular data from a screenshot image "
    "and output it as raw CSV. "
    "Rules:\n"
    "1. Output ONLY the CSV data — no greetings, no explanations, no markdown.\n"
    "2. Use comma as the column delimiter.\n"
    "3. Double-quote any field that contains a comma or a double-quote character.\n"
    "4. The FIRST row MUST be the column headers exactly as they appear.\n"
    "5. Leave empty cells blank (nothing between delimiters).\n"
    "6. Preserve every data row visible in the image.\n"
    "7. If the image does NOT contain a table with column headers, "
    'output exactly: NO_TABLE'
)

USER_PROMPT = (
    "The image below is a screenshot of tabular data. "
    "Extract every visible row and column as CSV. "
    "Output only the CSV. Do NOT wrap in ```csv markdown fences. "
    "Do NOT add any explanation before or after the CSV data."
)
