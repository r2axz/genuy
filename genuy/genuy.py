from warnings import catch_warnings, filterwarnings
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from pygad import GA

from .uysolution import UYSolution

def parse_args():
    arg_parser = ArgumentParser(description="A genetic algorithm optimization based Uda-Yagi antenna generator",
                                formatter_class=ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument(
        "--num-elements",
        "-n",
        type=int,
        default=4,
        help='Number of elements'
    )
    arg_parser.add_argument(
        "--element-radius",
        "-r",
        type=float,
        default=3.0,
        help="Radius of the element in mm"
    )
    arg_parser.add_argument(
        "--frequency",
        "-f",
        type=float,
        default=145.0,
        help="Target frequency in MHz"
    )
    arg_parser.add_argument(
        "--bandwidth",
        "-b",
        type=float,
        default=10.0,
        help="Bandwidth in MHz"
    )
    arg_parser.add_argument(
        "--reflector-length-min",
        type=float,
        default=0.5,
        help="Minimum length of the reflector element in terms of wavelength"
    )
    arg_parser.add_argument(
        "--reflector-length-max",
        type=float,
        default=0.6,
        help="Maximum length of the reflector element in terms of wavelength"
    )
    arg_parser.add_argument(
        "--driven-length-min",
        type=float,
        default=0.45,
        help="Minimum length of the driven element in terms of wavelength"
    )
    arg_parser.add_argument(
        "--driven-length-max",
        type=float,
        default=0.55,
        help="Maximum length of the driven element in terms of wavelength"
    )
    arg_parser.add_argument(
        "--director-length-min",
        type=float,
        default=0.4,
        help="Minimum length of the director elements in terms of wavelength"
    )
    arg_parser.add_argument(
        "--director-length-max",
        type=float,
        default=0.5,
        help="Maximum length of the director elements in terms of wavelength"
    )
    arg_parser.add_argument(
        "--spacing-min",
        type=float,
        default=0.025,
        help="Minimum spacing between elements in terms of wavelength"
    )
    arg_parser.add_argument(
        "--spacing-max",
        type=float,
        default=0.25,
        help="Maximum spacing between elements in terms of wavelength"
    )
    arg_parser.add_argument(
        "--num-generations",
        type=int,
        default=200,
        help="Maximum number of generations of the genetic algorithm"
    )
    arg_parser.add_argument(
        "--num-solutions",
        type=int,
        default=0,
        help="Number of solutions per population, "
        "if set to 0, it will be set to 10 times the number of genes (2 * num_elements - 1)"
    )
    arg_parser.add_argument(
        "--percent-mating",
        type=float,
        default=10.0,
        help="Percent of mating solutions in the population"
    )
    arg_parser.add_argument(
        "--mutation-percent-max",
        type=float,
        default=40.0,
        help="Max mutation percent of genes for adaptive mutation"
    )
    arg_parser.add_argument(
        "--mutation-percent-min",
        type=float,
        default=20.0,
        help="Min mutation percent of genes for adaptive mutation"
    )
    arg_parser.add_argument(
        "--num-segments",
        type=int,
        default=40,
        help="Number of wire segments"
    )
    arg_parser.add_argument(
        "--high-vswr-threshold",
        type=float,
        default=2.0,
        help="Threshold for high VSWR"
    )
    arg_parser.add_argument(
        "--high-vswr-penalty",
        type=float,
        default=-100.0,
        help="Fitness penalty for solutions with high VSWR"
    )
    arg_parser.add_argument(
        "--vswr-punish-early",
        action="store_true",
        default=False,
        help="Punish high VSWR early in the fitness evaluation"
    )
    arg_parser.add_argument(
        "--vswr-weight",
        type=float,
        default=100.0,
        help="Weight for VSWR in the fitness function"
    )
    arg_parser.add_argument(
        "--gain-weight",
        type=float,
        default=3.0,
        help="Weight for gain in the fitness function"
    )
    arg_parser.add_argument(
        "--fb-weight",
        type=float,
        default=1.0,
        help="Weight for front-to-back ratio in the fitness function"
    )
    arg_parser.add_argument(
        "--boom-length-weight",
        type=float,
        default=1.0,
        help="Weight for boom length in the fitness function"
    )
    arg_parser.add_argument(
        "--reference-impedance",
        "-z",
        type=complex,
        default=50.0+0j,
        help="Reference impedance for VSWR calculation"
    )
    arg_parser.add_argument(
        "--save-maa",
        type=str,
        default=None,
        help="Filename to save the best solution in MMANA format"
    )
    arg_parser.add_argument(
        "--plot-fitness",
        action="store_true",
        help="Plot fitness over generations"
    )
    return arg_parser.parse_args()

def fitness_function(ga_instance, solution, solution_idx):
    args = ga_instance.genuy_args
    uysolution = UYSolution(solution, element_radius=args.element_radius*1e-3)
    vswrs = list()
    gains = list()
    fbs = list()
    for f in [args.frequency - args.bandwidth/2, args.frequency, args.frequency + args.bandwidth/2]:
        uysolution.simulate(f, nseg=args.num_segments)
        vswr = uysolution.vswr(reference_impedance=args.reference_impedance)
        if args.vswr_punish_early and vswr >= args.high_vswr_threshold:
            return args.high_vswr_penalty
        vswrs.append(vswr)
        gains.append(uysolution.gain)
        fbs.append(uysolution.fb)
    worst_vswr = max(vswrs)
    worst_gain = min(gains)
    worst_fb = min(fbs)
    vswr_score = (1.0 / worst_vswr) * args.vswr_weight if worst_vswr < args.high_vswr_threshold else args.high_vswr_penalty
    gain_score = worst_gain * args.gain_weight
    fb_score = worst_fb * args.fb_weight
    boom_length_score = (1.0 / uysolution.boom_length) * args.boom_length_weight
    return vswr_score + gain_score + fb_score + boom_length_score

def on_generation(ga_instance):
    print(f"\rGeneration {ga_instance.generations_completed} of {ga_instance.num_generations}: Best Fitness = {ga_instance.best_solution()[1]:.2f}",
          end="", flush=True)

def main():
    args = parse_args()
    if args.num_elements < 2:
        raise ValueError("Number of elements must be at least 2")
    solution_length = 2 * args.num_elements - 1
    if args.num_solutions == 0:
        args.num_solutions = solution_length * 10
    elements_space = [
            {"low": args.reflector_length_min, "high": args.reflector_length_max},
            {"low": args.driven_length_min, "high": args.driven_length_max},
        ] + [{"low": args.director_length_min, "high": args.director_length_max}] * (args.num_elements - 2)
    spacings_space = [{"low": args.spacing_min, "high": args.spacing_max}] * (args.num_elements - 1)
    gene_space = [None] * solution_length
    gene_space[::2] = elements_space
    gene_space[1::2] = spacings_space
    ga_instance = GA(
        num_genes=solution_length,
        gene_space=gene_space,
        sol_per_pop=args.num_solutions,
        num_parents_mating=int(round((args.num_solutions / 100) * args.percent_mating)),
        num_generations=args.num_generations,
        parent_selection_type="tournament",
        K_tournament=2,
        keep_parents=2,
        crossover_type="single_point",
        mutation_type="adaptive",
        mutation_percent_genes=(args.mutation_percent_max, args.mutation_percent_min),
        parallel_processing=('process', None),
        fitness_func=fitness_function,
        on_generation=on_generation,
    )
    ga_instance.genuy_args = args
    ga_instance.run()
    solution, solution_fitness, solution_idx = ga_instance.best_solution()
    print("\nBest solution : ", solution)
    print("Best solution fitness : ", solution_fitness)
    print("Best solution index : ", solution_idx)
    uysolution = UYSolution(solution, element_radius=args.element_radius*1e-3)
    uysolution.simulate(args.frequency, nseg=args.num_segments)
    print("VSWR : ", uysolution.vswr(reference_impedance=args.reference_impedance))
    print("Impedance : ", uysolution.impedance)
    print("Gain : ", uysolution.gain)
    print("Front-to-Back Ratio : ", uysolution.fb)
    if args.save_maa:
        uysolution.save_to_maa(args.save_maa, frequency=args.frequency,
                               dm1=args.num_segments * 10, dm2=args.num_segments, sc=2.0, ec=2)
    
    if args.plot_fitness:
        with catch_warnings():
            filterwarnings("ignore", message="No artists with labels found")
            ga_instance.plot_fitness()
