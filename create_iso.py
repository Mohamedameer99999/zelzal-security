import os, re, pycdlib

SOURCE = r"F:\zelzal prog-AI"
OUTPUT = os.path.join(SOURCE, "AI_Task_Manager.iso")

iso = pycdlib.PyCdlib()
iso.new(interchange_level=3, joliet=3)

all_dirs = set()
all_files = []
for root, dirs, files in os.walk(SOURCE):
    for d in dirs:
        rel = os.path.relpath(os.path.join(root, d), SOURCE)
        all_dirs.add("/" + rel.replace("\\", "/"))
    for f in files:
        if f.endswith(".iso"):
            continue
        full = os.path.join(root, f)
        rel = os.path.relpath(full, SOURCE)
        all_files.append((full, "/" + rel.replace("\\", "/")))

def safe_name(name):
    return re.sub(r'[^A-Z0-9_]', '_', name.upper())

path_map = {"/": "/"}

# Map directories
for i, d in enumerate(sorted(all_dirs), 1):
    parent = os.path.dirname(d) or "/"
    parent_iso = path_map.get(parent, parent)
    raw = os.path.basename(d)
    safe = safe_name(raw)[:8]
    name = f"{safe}_{i:04d}" if safe else f"DIR_{i:04d}"
    name = name.strip(".")
    path_map[d] = parent_iso.rstrip("/") + "/" + name

# Map files
full_map = {}
for i, (full, jpath) in enumerate(all_files, 1):
    parent = os.path.dirname(jpath) or "/"
    parent_iso = path_map.get(parent, parent)
    fname = os.path.basename(jpath)
    base = safe_name(os.path.splitext(fname)[0])[:8]
    ext = safe_name(os.path.splitext(fname)[1].lstrip("."))[:3]
    if not base:
        base = "FILE"
    iso_name = f"{base}_{i:04d}.{ext}" if ext else f"{base}_{i:04d}"
    iso_name = iso_name.strip(".")
    ipath = parent_iso.rstrip("/") + "/" + iso_name
    path_map[jpath] = ipath
    full_map[jpath] = full

# Create dirs in breadth order
for d in sorted(all_dirs, key=lambda x: x.count("/")):
    ipath = path_map[d]
    print(f"  DIR: {ipath}  <- {d}")
    iso.add_directory(ipath, joliet_path=d)

# Add files  
for jpath, ipath in path_map.items():
    if jpath == "/" or jpath in all_dirs:
        continue
    full = full_map.get(jpath)
    print(f" FILE: {ipath}  <- {jpath}")
    iso.add_file(full, ipath, joliet_path=jpath)

iso.write(OUTPUT)
iso.close()
print(f"\nISO created: {OUTPUT}")
