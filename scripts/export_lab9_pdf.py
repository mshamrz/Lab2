import os
import subprocess
import markdown

ROOT_DIR = r"C:\Users\LEGION\Documents\GitHub\Lab2"
MD_PATH = os.path.join(ROOT_DIR, "LAB9_SUBMISSION.md")
HTML_PATH = os.path.join(ROOT_DIR, "LAB9_SUBMISSION.html")
PDF_PATH = os.path.join(ROOT_DIR, "LAB9_SUBMISSION.pdf")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

# Render Markdown to HTML
html_body = markdown.markdown(
    md_content,
    extensions=["tables", "fenced_code", "nl2br"]
)

# Full HTML template with printing CSS
html_document = f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8">
  <title>Звіт з лабораторної роботи 9: Spry on Google Cloud (and what it would cost)</title>
  <style>
    @page {{
      size: A4;
      margin: 16mm 14mm 16mm 14mm;
      @bottom-right {{
        content: counter(page);
      }}
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 10pt;
      line-height: 1.5;
      color: #1e293b;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }}
    h1 {{
      font-size: 19pt;
      color: #0f172a;
      border-bottom: 2.5px solid #0284c7;
      padding-bottom: 8px;
      margin-top: 0;
      margin-bottom: 12px;
    }}
    h2 {{
      font-size: 14pt;
      color: #0369a1;
      border-bottom: 1.5px solid #cbd5e1;
      padding-bottom: 5px;
      margin-top: 22px;
      margin-bottom: 10px;
      page-break-after: avoid;
    }}
    h3 {{
      font-size: 11.5pt;
      color: #0c4a6e;
      margin-top: 16px;
      margin-bottom: 6px;
      page-break-after: avoid;
    }}
    h4 {{
      font-size: 10.5pt;
      color: #334155;
      margin-top: 12px;
      margin-bottom: 4px;
      page-break-after: avoid;
    }}
    p, ul, ol {{
      margin-top: 4px;
      margin-bottom: 8px;
    }}
    li {{
      margin-bottom: 3px;
    }}
    hr {{
      border: 0;
      border-top: 1px solid #e2e8f0;
      margin: 14px 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 14px 0;
      font-size: 8.5pt;
      page-break-inside: avoid;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 5px 8px;
      text-align: left;
    }}
    th {{
      background-color: #f0fdf4;
      color: #065f46;
      font-weight: 600;
    }}
    tr:nth-child(even) td {{
      background-color: #f8fafc;
    }}
    code {{
      font-family: Consolas, "Liberation Mono", Menlo, Courier, monospace;
      font-size: 8.5pt;
      background-color: #f1f5f9;
      color: #0369a1;
      padding: 1px 4px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}
    pre {{
      background-color: #0f172a;
      color: #f8fafc;
      padding: 8px 10px;
      border-radius: 6px;
      font-size: 8pt;
      line-height: 1.4;
      overflow-x: auto;
      margin: 6px 0 10px 0;
      page-break-inside: avoid;
    }}
    pre code {{
      background: none;
      color: #e2e8f0;
      padding: 0;
      border: none;
      font-size: 8pt;
    }}
    blockquote {{
      background-color: #eff6ff;
      border-left: 4px solid #0284c7;
      margin: 8px 0;
      padding: 6px 12px;
      color: #075985;
      font-size: 9pt;
      page-break-inside: avoid;
    }}
  </style>
</head>
<body>
  {html_body}
</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_document)

print(f"HTML generated at: {HTML_PATH}")

# Convert HTML to PDF using Chrome Headless
temp_url = f"file:///{HTML_PATH.replace(os.sep, '/')}"
cmd = [
    CHROME_PATH,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF_PATH}",
    temp_url,
]

res = subprocess.run(cmd, capture_output=True, text=True)
if os.path.exists(PDF_PATH):
    size_kb = os.path.getsize(PDF_PATH) / 1024
    print(f"SUCCESS: PDF generated at {PDF_PATH} ({size_kb:.1f} KB)")
else:
    print(f"ERROR: Chrome failed to generate PDF: {res.stderr}")
