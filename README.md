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

**Antenna parameters**

| Option                        | Default  | Description                                         |
|-------------------------------|----------|-----------------------------------------------------|
| `-n`, `--num-elements`        | `4`      | Number of elements (reflector+driven+directors)     |
| `-f`, `--frequency`           | `145.0`  | Centre frequency, MHz                               |
| `-b`, `--bandwidth`           | `10.0`   | Optimization bandwidth, MHz                         |
| `-r`, `--element-radius`      | `3.0`    | Element radius, mm                                  |
| `-z`, `--reference-impedance` | `50+0j`  | Reference impedance for VSWR, Ω                     |

**GA and output parameters**

| Option                   | Default              | Description                                    |
|--------------------------|----------------------|------------------------------------------------|
| `--num-generations`      | `200`                | Maximum GA generations                         |
| `--num-solutions`        | `0` (auto: 10×genes) | Population size                                |
| `--percent-mating`       | `10.0`               | % of population selected as parents            |
| `--mutation-percent-max` | `40.0`               | Max gene mutation % (adaptive)                 |
| `--mutation-percent-min` | `20.0`               | Min gene mutation % (adaptive)                 |
| `--vswr-punish-early`    | *(off)*              | Return penalty on first bad-VSWR frequency     |
| `--seed`                 | *(random)*           | Random seed; printed so runs are reproducible  |
| `--save-maa`             | *(none)*             | Save best solution as MMANA `.maa` file        |
| `--plot-fitness`         | *(off)*              | Plot fitness vs. generation after run          |

Run `genuy --help` for the full option list.

### Per-element constraints

Use `--constrain-length` and `--constrain-spacing` to narrow the search space
for individual elements. Elements and spacings are numbered starting from 1.
Both options are repeatable.

```bash
# Fix element 1 (reflector) length range tightly, leave others free
genuy -n 5 -f 145 -b 10 --constrain-length 1 0.51 0.53

# Constrain spacing between elements 2 and 3
genuy -n 5 -f 145 -b 10 --constrain-spacing 2 0.10 0.15

# Multiple constraints
genuy -n 5 -f 145 -b 10 \
  --constrain-length 1 0.51 0.53 \
  --constrain-length 2 0.47 0.49 \
  --constrain-spacing 1 0.12 0.18
```

### Examples

Optimize a 4-element 145 MHz antenna and save the result:

```bash
genuy -n 4 -f 145 -b 10 --save-maa antenna.maa
```

Optimize a 6-element antenna, plot convergence, and save:

```bash
genuy -n 6 -f 145 -b 10 --num-generations 500 --save-maa 6el.maa --plot-fitness
```

Reproduce a previous run using a saved seed:

```bash
genuy -n 4 -f 145 -b 10 --seed 1234567890 --save-maa antenna.maa
```

## Fitness function

Each candidate solution is evaluated at three frequencies — lower band edge,
centre, and upper band edge. The fitness score is:

$$F = \begin{cases} \dfrac{w_\text{vswr}}{\text{VSWR}_\text{worst}} +
w_\text{gain} \cdot G_\text{worst} + w_\text{fb} \cdot \text{FB}_\text{worst} &
\text{if } \text{VSWR}_\text{worst} < \text{threshold} \\ p_\text{vswr} +
w_\text{gain} \cdot G_\text{worst} + w_\text{fb} \cdot \text{FB}_\text{worst} &
\text{otherwise} \end{cases}$$

Default weights: `vswr_weight=100`, `gain_weight=3.0`, `fb_weight=1.0`,
`boom_length_weight=1.0`. The hard VSWR penalty (`high_vswr_penalty=-100`)
discourages solutions that are badly mismatched anywhere in the band.

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
