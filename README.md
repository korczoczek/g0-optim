# g0-optim
Script optimizing G0 travel for CNC plotters, engavers and other XY based CNC machines, by solving the travelling salesman problem using the nearest neighbour method

Intended to be used with G-codes generated via https://github.com/sameer/svg2gcode , but should support any generic 2d G-codes

# Features
- Support for G2/G3 circular movement
- Automatic Metric/Imperial detection
- Automatic trimming of long float values
- Support for custon tool on/off sequences
- Support for custom program start/end sequences
- Optional line number generation

# Usage

```sh
python.exe g0-optim.py [options] input [output]
```

## Example
### Before
![Gcode with no G0 optimization](images/before.png)
### After
![Gcode with G0 optimization](images/after.png)
Gcode visualisation: https://ncviewer.com/