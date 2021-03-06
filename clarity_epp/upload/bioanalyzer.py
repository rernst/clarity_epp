"""Bioanalyzer results upload epp functions."""

import re

from genologics.entities import Process


def results(lims, process_id):
    """Upload bioanalyzer results to artifacts."""
    process = Process(lims, id=process_id)
    sample_measurements = {}

    # Parse File
    for output in process.all_outputs(unique=True):
        if output.name == 'Bioanalyzer Output':
            bioanalyzer_result_file = output.files[0]

            for line in lims.get_file_contents(bioanalyzer_result_file.id).split('\n'):
                if line.startswith('Sample Name'):
                    sample = line.rstrip().split(',')[1]
                elif line.startswith('Region 1'):
                    line = re.sub(r'"([0-9]+),([0-9\.]+)"', r'\1\2', line)  # Fix remove thousands seperator (,) and quotes ("")
                    size = line.rstrip().split(',')[5]
                    sample_measurements[sample] = int(size)

    # Set UDF
    for artifact in process.all_outputs():
        if artifact.name in sample_measurements:
            artifact.udf['Dx Fragmentlengte (bp)'] = sample_measurements[artifact.name]
            artifact.put()
