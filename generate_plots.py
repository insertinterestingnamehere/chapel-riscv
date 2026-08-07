import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Cairo')
from matplotlib import pyplot as plt
plt.style.use('seaborn-v0_8-colorblind')
# Publication/accessibility-oriented defaults
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans", "Helvetica"],
    "font.size": 12,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "legend.title_fontsize": 12,
    "axes.linewidth": 1.1,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})
import os
import shutil
from itertools import cycle
from matplotlib.ticker import LogLocator, LogFormatterSciNotation
import scipy.stats as stats

arch_map = {
    'MILK-V' : 'SG2042',
    'p550' : 'P550',
    'u74' : 'Unmatched',
    'icelake' : 'Ice Lake',
    'zen3' : 'Zen 3',
    'graniterapids' : 'Granite Rapids',
    'grace' : 'Grace',
    'qemu' : 'QEMU'}

benchmark_map = {
    'binarytrees4': 'Binary Trees (4)',
    'binarytrees5': 'Binary Trees (5)',
    'binarytrees-submitted': 'Binary Trees',
    'chameneosredux': 'Chameneos Redux',
    'chameneosredux-fast': 'Chameneos Redux (2)',
    'chop': 'ChOp',
    'fannkuch-redux-submitted': 'Fannkuch Redux',
    'fasta2': 'Fasta (2)',
    'fasta6': 'Fasta (6)',
    'fasta-submitted': 'Fasta',
    'knucleotide-hash': 'K-Nucleotide (Hash-Based)',
    'knucleotide-submitted': 'K-Nucleotide',
    'mandelbrot2': 'Mandelbrot (2)',
    'mandelbrot-submitted': 'Mandelbrot',
    'nbody3': 'N-Body (3)',
    'nbody4': 'N-Body (4)',
    'nbody-submitted': 'N-Body',
    'no-op': 'No-Op',
    'pidigits2-submitted': 'Digits of Pi (2)',
    'pidigits4-submitted': 'Digits of Pi (4)',
    'pidigits5-submitted': 'Digits of Pi (5)',
    'regexdnaredux-submitted-bytes': 'DNA Regex Redux (Bytes)',
    'regexdnaredux-submitted': 'DNA Regex Redux',
    'revcomp3-submitted': 'Reverse Complement (3)',
    'revcomp5-submitted': 'Reverse Complement (5)',
    'revcomp8-submitted': 'Reverse Complement (9)', # Historical naming discrepancy between Chapel and the CLBG site.
    'spectralnorm2-40000': 'Spectral Norm (V2, Size 40000)',
    'spectralnorm2': 'Spectral Norm (V2, Size 500)',
    'spectralnorm-submitted-40000': 'Spectral Norm (Size 40000)',
    'spectralnorm-submitted': 'Spectral Norm (Size 500)',
    'thread-ring-coforall-begin': 'Thread Ring (Coforall Begin)',
    'threadring': 'Thread Ring',
}

config_map = {'clbg_comparison':'Two-socket',
 'clbg_comparison_single_socket':'Single-socket',
 'clbg_comparison_single_socket_smt':'Single-socket with SMT',
 'clbg_comparison_smt':'Two-socket SMT'}

# The data loc structure and new loc structure assumes this is being run outside your data folder, not inside it.
# This matters because of dir finding, since we don't explicitly list the architectures we just assume the directories are the architectures.
# This is easily modified below
data_loc = '.'
new_data_loc = 'cleaned_data'
archlist = list(arch_map.keys())
#archlist = [arch for arch in os.listdir(data_loc) if os.path.isdir(f'{data_loc}/{arch}') and arch != '.git' and arch != new_data_loc]
# For now we only care about one llvm but again, this can be easily turned into a list in the following processing
llvm = 'llvm21'

# Make the new arch directories and llvm directories in the clean dataset
if not os.path.exists(new_data_loc):
    os.mkdir(new_data_loc)

plot_out_dir = 'plots'
if not os.path.exists(plot_out_dir):
    os.mkdir(plot_out_dir)

for arch in archlist:
    newarch = f'{new_data_loc}/{arch}'
    if not os.path.exists(newarch):
        os.mkdir(newarch)

    newllvm = f'{newarch}/{llvm}'
    if not os.path.exists(newllvm):
        os.mkdir(newllvm)

# Make the new config directories for the clean dataset
for arch in archlist:
    clbg_list = [config for config in os.listdir(f'{data_loc}/{arch}/{llvm}') if 'clbg' in config]
    if len(clbg_list) == 0:
        clbg_list = ['clbg_comparison']
    for config in clbg_list:
        newconfig = f'{new_data_loc}/{arch}/{llvm}/{config}'
        if not os.path.exists(f'{new_data_loc}/{arch}/{llvm}/{config}'):
            os.mkdir(f'{new_data_loc}/{arch}/{llvm}/{config}')

# Copy the appropriate dat files into their new clean locations
for arch in archlist:
    config_list = [f'{data_loc}/{arch}/{llvm}/{config}' for config in os.listdir(f'{data_loc}/{arch}/{llvm}') if 'clbg' in config]
    for config_path in config_list:
        for file in os.listdir(config_path):
            if 'dat' in file and 'perfSha' not in file:
                shutil.copy2(f'{config_path}/{file}', f'{config_path.replace(data_loc, new_data_loc)}/{file}')

    if len(config_list) == 0:
        config_path = f'{data_loc}/{arch}/{llvm}/'
        for file in os.listdir(config_path):
            if 'dat' in file and 'perfSha' not in file:
                shutil.copy2(f'{config_path}/{file}', f'{new_data_loc}/{arch}/{llvm}/{'clbg_comparison'}/{file}')

# Note that once you run all this, you could just load in the csv's instead of recreating the config dict from scratch each time.
config_dict = {}
for arch in os.listdir(new_data_loc):
    for llvm in os.listdir(f'{new_data_loc}/{arch}'):
        for config in os.listdir(f'{new_data_loc}/{arch}/{llvm}'):
            config_path = f'{new_data_loc}/{arch}/{llvm}/{config}'
            config_df = pd.DataFrame()
            for datfile in os.listdir(f'{config_path}'):
                if '.dat' in datfile:
                    fpath = f'{config_path}/{datfile}'
                    dat_df = pd.read_csv(fpath, sep=r"\s+", names=['date', 'data'], skiprows=1)
                    config_df[datfile.replace('.dat', '')] = dat_df['data'].tail(n=10).reset_index(drop=True)
                    # print(config_df)
            # Normalize by the mean of the no-op, aka the start-up time
            config_df = config_df - config_df['no-op'].mean()
            config_df.to_csv(f'{config_path}/{arch}_{llvm}_{config}_benchmark.csv', index=False)
            config_dict[(arch, llvm, config)] = config_df

# Get some stat summaries to recreate tables
single_llvm = 'llvm21'
archlist = ['grace', 'graniterapids', 'icelake', 'MILK-V', 'p550', 'u74', 'zen3']

mean_df = pd.concat([config_dict[(arch, 'llvm21', 'clbg_comparison')].mean() for arch in archlist], axis=1)
mean_df.columns = archlist

'''
# Not enough samples to normalize the standard deviation at this time
var_df = pd.concat([config_dict[(arch, 'llvm21', 'clbg_comparison')].var() for arch in archlist], axis=1)
var_df.columns = archlist
no_op_var = var_df.loc['no-op']
std_df = np.sqrt(var_df - no_op_var)
'''

max_df = pd.concat([config_dict[(arch, 'llvm21', 'clbg_comparison')].max() for arch in archlist], axis=1)
max_df.columns = archlist

min_df = pd.concat([config_dict[(arch, 'llvm21', 'clbg_comparison')].min() for arch in archlist], axis=1)
min_df.columns = archlist

vbenchmark_filenames = {
    "binarytrees": ["binarytrees-submitted", "binarytrees4", "binarytrees5"],
    "chameneos-redux": ["chameneosredux-fast", "chameneosredux"],
    "chop": ["chop"],
    "fannkuch-redux": ["fannkuch-redux-submitted"],
    "fasta": ["fasta-submitted", "fasta2", "fasta6"],
    "knucleotide": ["knucleotide-hash", "knucleotide-submitted"],
    "mandelbrot": ["mandelbrot-submitted", "mandelbrot2"],
    "nbody": ["nbody-submitted", "nbody3", "nbody4"],
    "no-op": ["no-op"],
    "pidigits": ["pidigits2-submitted", "pidigits4-submitted", "pidigits5-submitted"],
    "regexdna-redux": ["regexdnaredux-submitted-bytes", "regexdnaredux-submitted"],
    "revcomp": ["revcomp3-submitted", "revcomp5-submitted", "revcomp8-submitted"],
    "spectralnorm": ["spectralnorm-submitted-40000", "spectralnorm2-40000"],
    "thread-ring": ["threadring", "thread-ring-coforall-begin"],
}

group_titles = {
    'access-pattern': 'Binary Trees',
    'chop': 'ChOp',
    'float': 'Floating-Point-Intensive Benchmarks',
    'gmp': 'Extended-Precision Benchmark',
    'io': 'IO-Intensive Benchmarks',
    'integer': 'Integer-Intensive Benchmarks',
    'no-op': 'Chapel Startup Time',
    'synchronization' : 'Synchronization-Intensive Benchmarks'
}

benchmark_groups = {
    'access-pattern': sum((vbenchmark_filenames[name] for name in ['binarytrees']), []),
    'chop': sum((vbenchmark_filenames[name] for name in ['chop']), []),
    'float': sum((vbenchmark_filenames[name] for name in ['mandelbrot', 'nbody', 'spectralnorm']), []),
    'gmp': sum((vbenchmark_filenames[name] for name in ['pidigits']), []),
    'io': sum((vbenchmark_filenames[name] for name in ['fasta', 'knucleotide', 'regexdna-redux', 'revcomp']), []),
    'integer': sum((vbenchmark_filenames[name] for name in ['fannkuch-redux']), []),
    'no-op': sum((vbenchmark_filenames[name] for name in ['no-op']), []),
    'synchronization': sum((vbenchmark_filenames[name] for name in ['chameneos-redux', 'thread-ring']), []),
}

smt_benchmarks = sum([benchmark_groups[i] for i in benchmark_groups.keys() if i != 'no-op'], [])


# This is just for convenience, and for cleaning up the names for plotting purposes
mean_subtables = {}
for key in benchmark_groups.keys():
    mean_subtables[key] = mean_df.loc[benchmark_groups[key]].rename(columns=arch_map, index=benchmark_map)

# This should probably be in a helper file and called in a notebook, but it's fine to keep it here for now
def plot_parallel_coordinates_architectures(
    df,
    figsize=(14, 6),
    alpha=0.85,
    linewidth=2.0,
    markersize=6,
    title='',
    savepath=None
):
    """
    Accessibility- and publication-friendly parallel coordinate-style plot.

    Features:
      - x-axis: benchmarks
      - lines: architectures
      - y-values: performance speeds
      - color-vision-deficiency-conscious tab10 color palette
      - redundant encodings via markers and line styles
      - sans-serif fonts
      - minimum 12 pt text
      - right-side legend
      - publication-friendly export option

    Parameters
    ----------
    df : pandas.DataFrame
        Rows are benchmarks, columns are architectures, values are performance speeds.

    figsize : tuple
        Figure size.

    alpha : float
        Line transparency.

    linewidth : float
        Width of each line.

    markersize : float
        Size of markers.

    title : str
        Default '', the title for the plot

    savepath : str or None
        If provided, saves the figure to this path.
        For publication, prefer .pdf or .svg.
    """
    # This is not a line I would actually use
    data = df.apply(pd.to_numeric, errors="coerce")

    benchmarks = data.index.astype(str)
    architectures = data.columns.astype(str)
    x = np.arange(len(benchmarks))

    fig, ax = plt.subplots(figsize=figsize)

    # tab10 is generally color-vision-deficiency friendly for up to 10 categories.
    tab10_colors = plt.get_cmap("tab10").colors

    color_cycle = cycle(tab10_colors)
    linestyle_cycle = cycle(["-", "--", "-.", ":"])
    marker_cycle = cycle(["o", "s", "^", "D", "v", "P", "X", "*", "<", ">"])

    for arch in architectures:
        ax.plot(
            x,
            data[arch].values,
            color=next(color_cycle),
            linestyle=next(linestyle_cycle),
            marker=next(marker_cycle),
            linewidth=linewidth,
            markersize=markersize,
            alpha=alpha,
            label=str(arch),
            markeredgecolor="black",
            markeredgewidth=0.6
        )

    ax.set_xticks(x)
    ax.set_xticklabels(benchmarks, rotation=30, ha="right")

    #ax.set_xlabel("Benchmark")
    ax.set_ylabel("Time (s), Lower is Better")
    ax.set_title(title)

    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_major_formatter(LogFormatterSciNotation(base=10))

    # Grid designed to be visible but not dominant
    ax.grid(True, axis="y", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.grid(True, axis="x", linestyle=":", linewidth=0.5, alpha=0.25)

    # Reduce visual clutter
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Right-side legend
    ax.legend(
        title="Architecture",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
        borderaxespad=0.0
    )

    plt.tight_layout()

    if savepath is not None:
        plt.savefig(savepath, bbox_inches="tight")
        plt.clf()
    else:
        plt.show()

# For all the basic tables make a pretty little parallel coordinates plot.
for table in mean_subtables.keys():
    plot_parallel_coordinates_architectures(
    mean_subtables[table],
    figsize=(7,5),
    alpha=0.9,
    linewidth=2.2,
    markersize=6,
    title=group_titles[table],
    savepath=f'plots/{table}.pdf'
)

linestyles = [
    "solid",
    "dashdot",
    "dashed",
    "dotted",
    (0, (5, 1)),              # densely dashed
    (0, (3, 5, 1, 5)),        # dash-dot with wider spacing
    (0, (3, 1, 1, 1, 1, 1)),  # dash-dot-dot
]

config_list = ['clbg_comparison_single_socket', 'clbg_comparison_single_socket_smt', 'clbg_comparison', 'clbg_comparison_smt']

config_to_linestyle = {
    os.path.basename(config): linestyles[i % len(linestyles)]
    for i, config in enumerate(config_list)
}

for arch in archlist:
    try:
        plt.vlines(x=1, ymin=0, ymax=1, color='black', linestyle='-', linewidth=.5)
        key = (arch, llvm, 'clbg_comparison_single_socket')
        compare = config_dict[key][[i for i in smt_benchmarks if i in config_dict[key].columns]].mean()
        for key in [key for key in config_dict.keys() if key[0] == arch and key[2] != 'clbg_comparison_single_socket']:
            mean_vals = compare / config_dict[key][[i for i in smt_benchmarks if i in config_dict[key].columns]].mean()
            x = np.sort(mean_vals)
            y = np.arange(1, np.size(x) + 1) / np.size(x)
            plt.plot(x, y, label=config_map[key[2]], linestyle=config_to_linestyle[key[2]])

        #plt.xscale('log')
        #plt.xlim(0.001, 1000)
        plt.title('CDF for all Benchmarks on {}'.format(arch_map[arch]))
        # plt.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left", title='Config')
        plt.legend(loc='best', title='Config')

        plt.xlabel('Speedup Relative to Single-Socket Without SMT Config')
        plt.ylabel('Fraction of Benchmarks')
        if np.max(x) > 4:
            plt.xlim(right = 4)
        plt.tight_layout()
        plt.savefig(f'{plot_out_dir}/{arch}_smtnuma.pdf', bbox_inches="tight")
        plt.clf()
    except:
        pass

