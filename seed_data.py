import pandas as pd
import numpy as np
from db import get_connection

processors = ["Intel i3-10100", "Intel i5-10400", "Intel i5-12400", "Intel i7-11700", "AMD Ryzen 5 5600"]
ram_options = ["4GB", "8GB", "16GB"]
storage_options = ["256GB SSD", "512GB SSD", "1TB HDD"]
os_options = ["Windows 10", "Windows 11", "Ubuntu 22.04"]

labs = [f"Lab {i}" for i in range(1, 6)]
pcs_per_lab = 20

records = []
np.random.seed(42)

for lab in labs:
    for pc_num in range(1, pcs_per_lab + 1):
        record = {
            "asset_name": f"{lab} - PC {pc_num:02d}",
            "asset_type": "Desktop",
            "processor": np.random.choice(processors),
            "ram": np.random.choice(ram_options),
            "storage": np.random.choice(storage_options),
            "operating_system": np.random.choice(os_options),
            "pc_number": f"PC-{pc_num:02d}",
            "location": lab,
            "status": "Active"
        }
        records.append(record)

df = pd.DataFrame(records)
print(f"Generated {len(df)} PC records.")
print(df.head())

conn = get_connection()
cursor = conn.cursor()

insert_query = """
    INSERT INTO assets (asset_name, asset_type, processor, ram, storage, operating_system, pc_number, location, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df.iterrows():
    cursor.execute(insert_query, (
        row["asset_name"], row["asset_type"], row["processor"], row["ram"],
        row["storage"], row["operating_system"], row["pc_number"], row["location"], row["status"]
    ))

conn.commit()
conn.close()

print("All 100 PC records inserted successfully!")