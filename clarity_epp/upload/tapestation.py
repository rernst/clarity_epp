"""Tapestation results upload epp functions."""

from genologics.entities import Process


def results(lims, process_id):
    """Upload tapestation results to artifacts."""
    process = Process(lims, id=process_id)
    sample_measurements = {}

    # Parse File
    for output in process.all_outputs(unique=True):
        if output.name == 'TapeStation Output':
            tapestation_result_file = output.files[0]
            for line in lims.get_file_contents(tapestation_result_file.id).split('\n'):
                if line.startswith('FileName'):
                    header = line.split(',')
                    if 'Size [bp]' in header:
                        size_index = header.index('Size [bp]') # Tapestation compact peak table
                    else:
                        size_index = header.index('Average Size [bp]') # Tapestation compact region table
                    sample_index = header.index('Sample Description')

                elif line:
                    data = line.split(',')
                    sample = data[sample_index]
                    if sample != 'Ladder':
                        if data[size_index]:
                            size = int(data[size_index])
                            sample_measurements[sample] = size

    # Set UDF
    for artifact in process.all_outputs():
        if artifact.name not in ['TapeStation Output', 'TapeStation Samplesheet', 'TapeStation Sampleplots PDF']:
            sample_name = artifact.name.split('_')[0]
            if sample_name in sample_measurements:
                artifact.udf['Dx Fragmentlengte (bp)'] = sample_measurements[sample_name]
                artifact.put()
