import os
import re

base_dir = "/home/sscamarenas/Proyectos/Logistica Casa Lupita/App_Stealth/templates/dashboard"

for filename in os.listdir(base_dir):
    if filename.endswith("_form.html"):
        filepath = os.path.join(base_dir, filename)
        with open(filepath, "r") as f:
            content = f.read()
        
        # Replace form.submit() with form.requestSubmit()
        new_content = content.replace("form.submit()", "form.requestSubmit()")
        new_content = new_content.replace(".submit()", ".requestSubmit()") # Handle other cases like document.getElementById...submit()
        
        # Handle already replaced ones if I ran it multiple times
        new_content = new_content.replace(".requestSubmit()", "TEMPORARY_REPLACE_TOKEN")
        new_content = new_content.replace("TEMPORARY_REPLACE_TOKEN", ".requestSubmit()")
        
        if new_content != content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Updated JS submit in {filename}")
