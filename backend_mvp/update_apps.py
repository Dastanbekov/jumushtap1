import os

APPS_DIR = 'apps'
APPS = [
    'orders',
    'responses',
    'deals',
    'payments',
    'contracts',
    'reviews',
    'notifications'
]

for app in APPS:
    apps_py_path = os.path.join(APPS_DIR, app, 'apps.py')
    if os.path.exists(apps_py_path):
        content = f"""from django.apps import AppConfig


class {app.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app}'
"""
        with open(apps_py_path, 'w') as f:
            f.write(content)
        print(f"Updated {apps_py_path}")
    else:
        print(f"Skipping {apps_py_path} (not found)")
