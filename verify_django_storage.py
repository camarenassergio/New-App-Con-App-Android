import os
import django
from django.core.files.base import ContentFile

# Monkey patch pymysql for systems without mysqlclient (like local dev sometimes)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files.storage import default_storage

def verify_storage():
    print("Verifying Django Storage Configuration...")
    try:
        # 1. Print current settings used by storage
        print(f"Backend: {default_storage.__class__.__name__}")
        if hasattr(default_storage, 'endpoint_url'):
            print(f"Endpoint URL: {default_storage.endpoint_url}")
        if hasattr(default_storage, 'addressing_style'):
            print(f"Addressing Style: {default_storage.addressing_style}")
        
        # 2. Try to save a simple file
        print("\nAttempting to save 'django_test.txt'...")
        path = default_storage.save('django_test.txt', ContentFile(b'Hello from Django!'))
        print(f"File saved successfully at: {path}")
        
        # 3. Try to get URL
        url = default_storage.url(path)
        print(f"File URL: {url}")
        
        # 4. Clean up
        print("\nCleaning up...")
        default_storage.delete(path)
        print("File deleted.")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_storage()
