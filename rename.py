import os
import pandas as pd

CSV_FILE = "products_export_1 (1).csv"      # Adjust if you rename
FOLDER_BASE = "image-video"

df = pd.read_csv(CSV_FILE)
handles = df["Handle"].tolist()

renamed = 0
created = 0

for idx, handle in enumerate(handles):
    folder_num = str(idx+1)
    old_folder = os.path.join(FOLDER_BASE, folder_num)
    new_folder = os.path.join(FOLDER_BASE, handle)
    if os.path.isdir(old_folder):
        if not os.path.exists(new_folder):
            print(f"Renaming {old_folder} -> {new_folder}")
            os.rename(old_folder, new_folder)
            renamed += 1
        else:
            print(f"Target folder {new_folder} already exists, skipping rename.")
    elif not os.path.exists(new_folder):
        print(f"Creating empty {new_folder}")
        os.makedirs(new_folder)
        created += 1
    else:
        print(f"Folder {new_folder} already exists.")
print(f"Done! Renamed {renamed} folders, created {created} new handle-named folders.")
