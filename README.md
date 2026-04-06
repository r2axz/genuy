# genuy

A genetic algorithm-based Uda-Yagi antenna optimizer. Uses
[PyGAD](https://pygad.readthedocs.io/) as the GA engine and
[pymininec](https://github.com/schlatterbeck/pymininec) for antenna simulation
to evolve element lengths and spacings that maximise gain, front-to-back ratio,
and VSWR across a specified bandwidth.

## Features

- Optimizes reflector, driven element, and an arbitrary number of director
  elements
- Evaluates fitness across the full bandwidth (low edge, centre, high edge) to
  avoid narrow-band solutions
- Adaptive mutation and tournament selection for robust multimodal search
- Parallel fitness evaluation using all available CPU cores
- Exports the best solution as an [MMANA-GAL](http://gal-ana.de/basicmm/en/)
  `.maa` file

## Requirements

- Python ≥ 3.14
- [pymininec](https://pypi.org/project/pymininec/) ≥ 1.2.0
- [pygad](https://pypi.org/project/pygad/) ≥ 3.5.0

## Installation

```bash
pip install genuy
```

Or from source:

```bash
git clone https://github.com/r2axz/genuy
cd genuy
pip install .
```

## Usage

```
genuy [OPTIONS]
```

### Key options

| Option | Default | Description |
|---|---|---|
| `-n`, `--num-elements` | `4` | Total number of elements (reflector + driven + directors) |
| `-f`, `--frequency` | `145.0` MHz | Target centre frequency |
| `-b`, `--bandwidth` | `10.0` MHz | Bandwidth over which to optimise |
| `-r`, `--element-radius` | `3.0` mm | Physical radius of all elements |
| `-z`, `--reference-impedance` | `50+0j` Ω | Reference impedance for VSWR calculation |
| `--num-generations` | `1000` | Maximum number of GA generations |
| `--num-solutions` | `100` | Population size |
| `--percent-mating` | `10.0` | Percentage of population selected as parents |
| `--save-maa` | *(none)* | Save best solution to an MMANA `.maa` file |
| `--plot-fitness` | *(off)* | Plot fitness vs. generation after the run |

Run `genuy --help` for the full list of options including element length bounds,
spacing bounds, mutation rates, VSWR penalty settings, and wire segmentation.

### Examples

Optimize a 4-element 145 MHz antenna and save the result:

```bash
genuy -n 4 -f 145 -b 10 --save-maa antenna.maa
```

Optimize a 6-element antenna, plot convergence, and save:

```bash
genuy -n 6 -f 145 -b 10 --num-generations 1000 --num-solutions 150 --save-maa 6el.maa --plot-fitness
```

## Fitness function

Each candidate solution is evaluated at three frequencies — lower band edge,
centre, and upper band edge. The fitness score is:

$$F = \begin{cases} \dfrac{w_\text{vswr}}{\text{VSWR}_\text{worst}} +
w_\text{gain} \cdot G_\text{worst} + w_\text{fb} \cdot \text{FB}_\text{worst} &
\text{if } \text{VSWR}_\text{worst} < \text{threshold} \\ p_\text{vswr} +
w_\text{gain} \cdot G_\text{worst} + w_\text{fb} \cdot \text{FB}_\text{worst} &
\text{otherwise} \end{cases}$$

Default weights: `vswr_weight=100`, `gain_weight=1.0`, `fb_weight=2.0`. The hard
VSWR penalty (`high_vswr_penalty=-100`) discourages solutions that are badly
mismatched anywhere in the band.

## Output

After the run the best solution is printed to stdout:

```
Best solution :  [0.512 0.18 0.474 0.15 0.452 0.19 0.438]
Best solution fitness :  47.23
VSWR :  1.34
Impedance :  (42.1+3.2j)
Gain :  10.8
Front-to-Back Ratio :  18.4
```

## License

MIT — see [LICENSE](LICENSE).
