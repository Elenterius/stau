# Star Trek Armada Python Utilities
Python scripts for reading/writing odf and sod model files.

# Storm3D SOD (.sod) Files
### SodIO - read & write sod files
```python
sod_io = SodIO()

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
Supported SOD Versions:
- 1.61 maybe?
- 1.7 maybe?
- 1.8
- 1.90, 1.91, 1.92, 1.93
 
mileage may vary :shrug:
 
Try it out and let me know what works.

### Blender Addon
Import SOD models with all the hardpoints, etc.

Blender Version: 2.8.x

##### TODO:
- [ ] add sod export capabilities
- [ ] remove hacky import & make it a proper addon

# ODF Files
#### ODF Parser
Returns a dict containing the compiled result of an odf including all parent odfs.
