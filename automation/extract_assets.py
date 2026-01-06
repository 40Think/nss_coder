
import re
import os

FILE_PATH = "voice_server.py"

print(f"Reading {FILE_PATH}...")
with open(FILE_PATH, "r") as f:
    content = f.read()

# 1. Locate INDEX_HTML block
start_marker = 'INDEX_HTML = """<!DOCTYPE html>'
start_idx = content.find(start_marker)

if start_idx == -1:
    print("ERROR: Start marker not found!")
    exit(1)

# Find the end of the triple-quoted string
# We search starting from right after the assignment
content_after_start = content[start_idx + len('INDEX_HTML = """'):]
end_idx = content_after_start.find('"""')

if end_idx == -1:
    print("ERROR: End marker not found!")
    exit(1)

html_raw = content_after_start[:end_idx]
print(f"Found HTML block length: {len(html_raw)}")

# 2. Extract CSS
css_pattern = re.compile(r'<style>(.*?)</style>', re.DOTALL)
css_match = css_pattern.search(html_raw)
if css_match:
    css_content = css_match.group(1).strip()
    with open("static/css/style.css", "w") as f:
        f.write(css_content)
    print(f"Extracted static/css/style.css ({len(css_content)} chars)")
    
    # Replace in HTML
    html_raw = css_raw = css_match.group(0) # The full <style>...</style> block
    html_new = html_raw.replace(css_raw, '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">')
else:
    print("WARNING: No CSS found")
    html_new = html_raw

# 3. Extract JS
# Find the script tag. Note: There might be multiple? The file showed one big script at the end.
# We'll look for the last script tag or the one containing "STATE" as seen in the view_file output.
js_pattern = re.compile(r'<script>(.*?)</script>', re.DOTALL)
js_match = js_pattern.search(html_new)
 
if js_match:
    js_content = js_match.group(1).strip()
    with open("static/js/app.js", "w") as f:
        f.write(js_content)
    print(f"Extracted static/js/app.js ({len(js_content)} chars)")
    
    # Replace in HTML
    js_raw = js_match.group(0)
    html_new = html_new.replace(js_raw, '<script src="{{ url_for(\'static\', filename=\'js/app.js\') }}"></script>')
else:
    print("WARNING: No JS found")

# 4. Save HTML
with open("templates/index.html", "w") as f:
    f.write(html_new)
print(f"Extracted templates/index.html ({len(html_new)} chars)")

# 5. Update voice_server.py
# Remove the INDEX_HTML constant
# We replace the whole block (start_marker ... end_idx + """) with a comment
block_len = len('INDEX_HTML = """') + end_idx + 3
replacement = '# INDEX_HTML moved to templates/index.html\n# INDEX_HTML = "" # Removed'

new_content = content[:start_idx] + replacement + content[start_idx + block_len:]

# Fix imports
if "from flask import Flask, request, jsonify, send_from_directory, Response" in new_content:
    new_content = new_content.replace(
        "from flask import Flask, request, jsonify, send_from_directory, Response",
        "from flask import Flask, request, jsonify, send_from_directory, Response, render_template"
    )
else:
    print("WARNING: Could not find Flask import line to update. Please check manually.")

# Fix route
if "return Response(INDEX_HTML, mimetype='text/html')" in new_content:
    new_content = new_content.replace("return Response(INDEX_HTML, mimetype='text/html')", "return render_template('index.html')")
    print("Updated Response(...) route to use render_template")
elif "return INDEX_HTML" in new_content:
    new_content = new_content.replace("return INDEX_HTML", "return render_template('index.html')")
    print("Updated direct return route to use render_template")
else:
    print("WARNING: Could not find 'return INDEX_HTML' or 'Response(...)' to update. Please check manually.")

# Write back
with open(FILE_PATH, "w") as f:
    f.write(new_content)
print("Updated voice_server.py")
