# Star Trek Armada Python Utilities
Python scripts for reading/writing Start Trek Armada SOD model files.

# Storm3D SOD (.sod) Files
**custom SOD parser/builder without external dependencies**
```python
sod_io = SodIO() # sod_io.py

# parse sod file
file_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\fbattle.sod'
sod: Sod = sod_io.read_file(file_path)

...

# export sod as json
with open('../dump/fbattle.json', 'w') as outfile:
    json.dump(sod.to_dict(), outfile)

...

# write sod obj to file
sod_io.write_file(sod, '../dump/fbattle.sod')
```
**SOD parser/builder script using the construct library**
```python
from construct import *
from sod_construct_io import sod_format 

file_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\fconst.sod'

with open(file_path, 'rb') as binary_io:
    sod_container: Container = sod_format.parse_stream(binary_io)

version: float = sod_container.get("version")
data: Container = sod_container.get("data")
nodes: ListContainer = data.get("nodes")

...

sod_format.build_file({...}, '../dump/fconst.sod')
```
Supported SOD Versions:
- 1.6
- 1.7
- 1.8
- 1.90, 1.91, 1.92, 1.93
 
mileage may vary :shrug:
 
Try it out and let me know what doesn't works.

### Blender Addon [WIP]
Import SOD models with all the hardpoints, etc.

Blender Version: 2.8.x

##### TODO:
- [ ] add sod export capabilities
- [ ] remove hacky import & make it a proper addon

# ODF Files
#### ODF Parser
Returns a dict containing the compiled result of an odf including all parent odfs.
