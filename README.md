# g0-optim
Script optimizing G0 travel for CNC plotters, engavers and other XY based CNC machines, by solving the travelling salesman problem using the nearest neighbour method

Intended to be used with https://github.com/sameer/svg2gcode , but should support any generic 2d G-code

# Features
- Support for G2/G3 circular movement
- Automatic Metric/Imperial detection
- Automatic trimming of long float values

# Usage

```sh
python.exe g0-optim.py [options] input [output]
```
