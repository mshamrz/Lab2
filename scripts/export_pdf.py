import os
import re
import subprocess
import markdown

ROOT_DIR = r"C:\Users\LEGION\Documents\GitHub\Lab2"
MD_PATH = os.path.join(ROOT_DIR, "LAB8_SUBMISSION.md")
HTML_PATH = os.path.join(ROOT_DIR, "LAB8_SUBMISSION.html")
PDF_PATH = os.path.join(ROOT_DIR, "LAB8_SUBMISSION.pdf")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

# Replace mermaid code block with a styled visual architecture diagram
svg_diagram = """
<div class="diagram-container">
  <div class="diagram-title">Cloud Streaming Pipeline Architecture (Part 4)</div>
  <svg viewBox="0 0 820 220" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#1d4ed8;stop-opacity:1" />
      </linearGradient>
      <linearGradient id="gradS3" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#047857;stop-opacity:1" />
      </linearGradient>
      <linearGradient id="gradAlert" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#d97706;stop-opacity:1" />
      </linearGradient>
      <linearGradient id="gradSNS" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#ef4444;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#b91c1c;stop-opacity:1" />
      </linearGradient>
      <linearGradient id="gradAthena" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#6d28d9;stop-opacity:1" />
      </linearGradient>
      <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 8 5 L 0 9 z" fill="#64748b" />
      </marker>
    </defs>

    <!-- Producer Node -->
    <rect x="20" y="70" width="140" height="70" rx="8" fill="url(#grad1)" />
    <text x="90" y="100" fill="#fff" font-family="Segoe UI, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Producer</text>
    <text x="90" y="122" fill="#e0e7ff" font-family="Segoe UI, sans-serif" font-size="11" text-anchor="middle">(Python Micro-batches)</text>

    <!-- Arrow Producer -> Ingestion -->
    <path d="M 160 105 L 210 105" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

    <!-- Ingestion & Buffer -->
    <rect x="220" y="70" width="150" height="70" rx="8" fill="url(#grad1)" />
    <text x="295" y="100" fill="#fff" font-family="Segoe UI, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Stream Buffer</text>
    <text x="295" y="122" fill="#e0e7ff" font-family="Segoe UI, sans-serif" font-size="11" text-anchor="middle">payments-stream/</text>

    <!-- Arrow Ingestion -> S3 -->
    <path d="M 370 95 L 430 55" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

    <!-- Arrow Ingestion -> Monitor -->
    <path d="M 370 120 L 430 155" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

    <!-- S3 Storage -->
    <rect x="440" y="20" width="160" height="65" rx="8" fill="url(#gradS3)" />
    <text x="520" y="47" fill="#fff" font-family="Segoe UI, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Amazon S3 Lake</text>
    <text x="520" y="68" fill="#d1fae5" font-family="Segoe UI, sans-serif" font-size="10.5" text-anchor="middle">JSON Micro-batches</text>

    <!-- Real-time Monitor -->
    <rect x="440" y="130" width="160" height="65" rx="8" fill="url(#gradAlert)" />
    <text x="520" y="157" fill="#fff" font-family="Segoe UI, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Real-time Monitor</text>
    <text x="520" y="178" fill="#fef3c7" font-family="Segoe UI, sans-serif" font-size="10.5" text-anchor="middle">Failure Rate &gt; 10%</text>

    <!-- Arrow S3 -> Athena -->
    <path d="M 600 52 L 650 52" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

    <!-- Amazon Athena -->
    <rect x="660" y="20" width="140" height="65" rx="8" fill="url(#gradAthena)" />
    <text x="730" y="47" fill="#fff" font-family="Segoe UI, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Amazon Athena</text>
    <text x="730" y="68" fill="#ede9fe" font-family="Segoe UI, sans-serif" font-size="10.5" text-anchor="middle">payments_stream SQL</text>

    <!-- Arrow Monitor -> SNS -->
    <path d="M 600 162 L 650 162" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

    <!-- Amazon SNS -->
    <rect x="660" y="130" width="140" height="65" rx="8" fill="url(#gradSNS)" />
    <text x="730" y="157" fill="#fff" font-family="Segoe UI, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Amazon SNS</text>
    <text x="730" y="178" fill="#fee2e2" font-family="Segoe UI, sans-serif" font-size="10.5" text-anchor="middle">Email Notifications</text>
  </svg>
</div>
"""

# Replace the ```mermaid ... ``` section with the styled SVG
md_content_processed = re.sub(r"```mermaid[\s\S]*?```", svg_diagram, md_content)

# Render Markdown to HTML
html_body = markdown.markdown(
    md_content_processed,
    extensions=["tables", "fenced_code", "nl2br"]
)

# Full HTML template with printing CSS
html_document = f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8">
  <title>Звіт з лабораторної роботи 8: Streaming and Batch Analytics</title>
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
      border-bottom: 2.5px solid #2563eb;
      padding-bottom: 8px;
      margin-top: 0;
      margin-bottom: 12px;
    }}
    h2 {{
      font-size: 14pt;
      color: #1e3a8a;
      border-bottom: 1.5px solid #cbd5e1;
      padding-bottom: 5px;
      margin-top: 22px;
      margin-bottom: 10px;
      page-break-after: avoid;
    }}
    h3 {{
      font-size: 11.5pt;
      color: #1e40af;
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
      background-color: #f1f5f9;
      color: #0f172a;
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
      border-left: 4px solid #3b82f6;
      margin: 8px 0;
      padding: 6px 12px;
      color: #1e3a8a;
      font-size: 9pt;
      page-break-inside: avoid;
    }}
    .diagram-container {{
      border: 1.5px solid #cbd5e1;
      background: #f8fafc;
      border-radius: 8px;
      padding: 12px;
      margin: 12px 0;
      text-align: center;
      page-break-inside: avoid;
    }}
    .diagram-title {{
      font-size: 11pt;
      font-weight: bold;
      color: #1e293b;
      margin-bottom: 8px;
    }}
    .header-box {{
      background: #f8fafc;
      border-left: 4px solid #2563eb;
      padding: 8px 12px;
      margin-bottom: 14px;
      border-radius: 0 6px 6px 0;
      font-size: 9.5pt;
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
