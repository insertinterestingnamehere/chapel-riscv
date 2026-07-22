from collections import OrderedDict
import statistics

available_arches = ['MILK-V', 'p550', 'grace', 'zen3', 'graniterapids', 'icelake']

numa_only_arches = ['grace']
smt_only_arches = []
numa_and_smt_arches = ['zen3', 'graniterapids', 'icelake']
numa_or_smt_arches = numa_only_arches + smt_only_arches + numa_and_smt_arches

arch_names = {
    'MILK-V' : 'SG2042',
    'p550' : 'P550',
    'icelake' : 'Ice Lake',
    'zen3' : 'Zen 3',
    'graniterapids' : 'Granite Rapids',
    'grace' : 'Grace'}

# Map the inconsistent file names to something more consistent
# and suitable for being displayed in a paper table.
# Some explanation about there being many versions will still
# be needed, but this should at least make things look nicer.
display_names = {
    'binarytrees4.dat' : 'Binary Trees (4)',
    'binarytrees5.dat' : 'Binary Trees (5)',
    'binarytrees-submitted.dat' : 'Binary Trees',
    'chameneosredux.dat' : 'Chameneos Redux',
    'chameneosredux-fast.dat' : 'Chameneos Redux (2)',
    'fannkuch-redux-submitted.dat' : 'Fannkuch Redux',
    'fasta2.dat' : 'Fasta (2)',
    'fasta6.dat' : 'Fasta (6)',
    'fasta-submitted.dat' : 'Fasta',
    'knucleotide-hash.dat' : 'K-Nucleotide (Hash-Based)',
    'knucleotide-submitted.dat' : 'K-Nucleotide',
    'mandelbrot2.dat' : 'Mandelbrot (2)',
    'mandelbrot-submitted.dat' : 'Mandelbrot',
    'nbody3.dat' : 'N-Body (3)',
    'nbody4.dat' : 'N-Body (4)',
    'nbody-submitted.dat' : 'N-Body',
    'no-op.dat' : 'No-Op',
    'pidigits2-submitted.dat' : 'Digits of Pi (2)',
    'pidigits4-submitted.dat' : 'Digits of Pi (4)',
    'pidigits5-submitted.dat' : 'Digits of Pi (5)',
    'regexdnaredux-submitted-bytes.dat' : 'DNA Regex Redux (Bytes)',
    'regexdnaredux-submitted.dat' : 'DNA Regex Redux',
    'revcomp3-submitted.dat' : 'Revcomp (3)',
    'revcomp5-submitted.dat' : 'Revcomp (5)',
    'revcomp8-submitted.dat' : 'Revcomp (8)',
    'spectralnorm2-40000.dat' : 'Spectral Norm (V2, Size 40000)',
    'spectralnorm2.dat' : 'Spectral Norm (V2, Size 500)',
    'spectralnorm-submitted-40000.dat' : 'Spectral Norm (Size 40000)',
    'spectralnorm-submitted.dat' : 'Spectral Norm (Size 500)',
    'thread-ring-coforall-begin.dat' : 'Thread Ring (Coforall Begin)',
    'threadring.dat' : 'Thread Ring'}

benchmark_filenames = OrderedDict([
    ('binarytrees',
        ('binarytrees-submitted.dat',
         'binarytrees4.dat',
         'binarytrees5.dat')),
    ('chameneos-redux',
        ('chameneosredux-fast.dat',
         'chameneosredux.dat')),
    ('fannkuch-redux',
        ('fannkuch-redux-submitted.dat',)),
    ('fasta',
        ('fasta-submitted.dat',
         'fasta2.dat',
         'fasta6.dat')),
    ('knucleotide',
        ('knucleotide-hash.dat',
         'knucleotide-submitted.dat')),
    ('mandelbrot',
        ('mandelbrot-submitted.dat',
         'mandelbrot2.dat')),
    ('nbody',
        ('nbody-submitted.dat',
         'nbody3.dat',
         'nbody4.dat')),
    ('no-op',
        ('no-op.dat',)),
    ('pidigits',
        ('pidigits2-submitted.dat',
         'pidigits4-submitted.dat',
         'pidigits5-submitted.dat')),
    ('regexdna-redux',
        ('regexdnaredux-submitted-bytes.dat',
         'regexdnaredux-submitted.dat')),
    ('revcomp',
        ('revcomp3-submitted.dat',
         'revcomp5-submitted.dat',
         'revcomp8-submitted.dat')),
    ('spectralnorm',
        ('spectralnorm-submitted-40000.dat',
         'spectralnorm-submitted.dat',
         'spectralnorm2-40000.dat',
         'spectralnorm2.dat')),
    ('thread-ring',
        ('threadring.dat',
         'thread-ring-coforall-begin.dat'))])

benchmark_groups = OrderedDict([
    ('acces-pattern', ('binarytrees',)),
    ('float', ('mandelbrot', 'nbody', 'spectralnorm')),
    ('gmp', ('pidigits',)),
    ('io', ('fasta', 'knucleotide', 'regexdna-redux', 'revcomp')),
    ('integer', ('fannkuch-redux',)),
    ('no-op', ('no-op',)),
    ('synchronization', ('chameneos-redux', 'thread-ring'))])

def aggregate_runs(full_fname, method = 'mean', na_default = 'n/a'):
    if method == 'mean':
        aggregate = statistics.mean
    elif method == 'median':
        aggregate = statistics.median
    else:
        raise ValueError('Aggregation method not recognized')
    try:
        with open(full_fname) as f:
            vals = [float(line.split()[1]) for line in f.readlines()[1:]]
    except FileNotFoundError:
        return na_default
    agg = aggregate(vals)
    return "{:.2f}".format(agg)

table_template = '''\\begin{{table*}}[t]
\\begin{{center}}
\\begin{{tabular}}{{{}}}
\\hline
{}
\\hline
{}
\\hline
\\end{{tabular}}
\\end{{center}}
\\end{{table*}}'''

def generate_table_for_group(group, arches = available_arches, llvmver = 20):
    benchmarks = benchmark_groups[group]
    datfiles = [fname for bench in benchmark_groups[group]
                      for fname in benchmark_filenames[bench]]
    table_format = '|c|{}|'.format(' '.join(['c' for a in arches]))
    table_header = "Name & {} \\\\".format(" & ".join(arch_names[arch] for arch in arches))
    rows = []
    for datfile in datfiles:
        entries = []
        for arch in arches:
            if arch in ['MILK-V', 'p550']:
                entries.append(aggregate_runs("{}/llvm{}/{}".format(arch, llvmver, datfile)))
            else:
                entries.append(aggregate_runs('{}/llvm{}/clbg_comparison/{}'.format(arch, llvmver, datfile)))
        rows.append("{} & {} \\\\".format(display_names[datfile], ' & '.join(entries)))
    table_body = "\n".join(rows)
    return table_template.format(table_format, table_header, table_body)

smtnuma_table_template = '''\\addtolength{\\tabcolsep}{-0.4em}
\\begin{{table*}}[t]
\\begin{{center}}
\\begin{{tabular}}{{{}}}
\\hline
{}
\\hline
{}
\\hline
{}
\\end{{tabular}}
\\end{{center}}
\\end{{table*}}
\\addtolength{\\tabcolsep}{0.4em}'''

# Just do all the arches instead of allowing the caller to specify a subset.
def generate_smt_table(llvmver = 20):
    table_format = '|c|{}|'.format('|'.join('c c c c' if arch in numa_and_smt_arches else 'c c' for arch in numa_or_smt_arches))
    arch_header_entries = []
    arch_header_template = '\\multicolumn{{{}}}{{|c|}}{{{}}}'
    config_header_entries = []
    for arch in numa_or_smt_arches:
        if arch in numa_and_smt_arches:
            arch_header_entries.append(arch_header_template.format(4, arch_names[arch]))
            config_header_entries.extend(['ss', 'sssmt', '2s', '2ssmt'])
        elif arch in smt_only_arches:
            arch_header_entries.append(arch_header_template.format(2, arch_names[arch]))
            config_header_entries.extend(['nsmt', 'smt'])
        else:
            assert arch in numa_only_arches
            arch_header_entries.append(arch_header_template.format(2, arch_names[arch]))
            config_header_entries.extend(['ss', '2s'])
    arch_header = 'Name: & {} \\\\'.format(' & '.join(arch_header_entries))
    config_header = 'Config: & {} \\\\'.format(' & '.join(config_header_entries))

    entry_lines = []
    data_line_template = '{} & {} \\\\'
    numa_and_smt_folders = ['clbg_comparison_single_socket',
                            'clbg_comparison_single_socket_smt',
                            'clbg_comparison',
                            'clbg_comparison_smt']
    numa_only_folders = ['clbg_comparison_single_socket', 'clbg_comparison']
    smt_only_folders = ['clbg_comparison', 'clbg_comparison_smt']
    for group in benchmark_groups:
        datfiles = [fname for bench in benchmark_groups[group]
                    for fname in benchmark_filenames[bench]]
        for datfile in datfiles:
            entries = []
            for arch in numa_or_smt_arches:
                if arch in numa_and_smt_arches:
                    folders = numa_and_smt_folders
                elif arch in numa_only_arches:
                    folders = numa_only_folders
                else:
                    folders = smt_only_folders
                for folder in folders:
                    entries.append(aggregate_runs("{}/llvm{}/{}/{}".format(arch, llvmver, folder, datfile)))
            entry_lines.append(data_line_template.format(display_names[datfile], ' & '.join(entries)))
        entry_lines.append('\\hline')
    data_lines = '\n'.join(entry_lines)
    return smtnuma_table_template.format(table_format, arch_header, config_header, data_lines)

if __name__ == '__main__':
    for group in benchmark_groups:
        print(generate_table_for_group(group))
        print()
    for llvmver in [20, 21, 22]:
        print(generate_smt_table(llvmver))
        print()
