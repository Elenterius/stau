# Star Trek Armada Python Utilities
Python scripts for reading/writing odf and sod model files.

# ODF Files
#### ODF Parser
Returns a dict containing the compiled result of an odf including all parent odfs.

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
Supported SOD Versions: 1.8 & 1.9
 
Might be able to read other versions, mileage may vary :shrug:
 - Versions should be greater than 1.6001
 
 Try it out and let me know what works.
### Blender Addon
Import SOD models with all the hardpoints, etc.

Blender Version: 2.8.x

##### TODO:
- [ ] add sod export capabilities
- [ ] remove hacky import & make it a proper addon
