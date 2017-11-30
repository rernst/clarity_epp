"""Sample upload epp functions."""
from genologics.entities import Sample, Project, Containertype, Container, Researcher, Workflow

import utils


def from_helix(lims, input_file):
    """Upload samples from helix export file."""
    # Create project
    project_name = input_file.name.rstrip('.csv').split('/')[-1]
    if not lims.get_projects(name=project_name):
        researcher = Researcher(lims, id='254')  # DX_EPP user
        #project = Project.create(lims, name=project_name, researcher=researcher, udf={'Application': 'DX'})

    container_type = Containertype(lims, id='2')  # Tube

    # match header and udf fields
    udf_column = {
        'Dx Onderzoeknummer': {'column': 'Onderzoeknummer'},
        'Dx Fractienummer': {'column': 'Fractienummer'},
        'Dx Monsternummer': {'column': 'Monsternummer'},
        'Dx Concentratie (ng/ul)': {'column': 'Concentratie (ng/ul)'},
        'Dx Materiaal type': {'column': 'Materiaal'},
        'Dx Foetus': {'column': 'Foetus'},
        'Dx Foetus geslacht': {'column': 'Foetus_geslacht'},
        'Dx Overleden': {'column': 'Overleden'},
        'Dx Opslaglocatie': {'column': 'Opslagpositie'},
        'Dx Spoed': {'column': 'Spoed'},
        'Dx NICU Spoed': {'column': 'NICU Spoed'},
        'Dx Persoons ID': {'column': 'Persoons_id'},
        'Dx Werklijstnummer': {'column': 'Werklijstnummer'},
        'Dx Unummer': {'column': 'Familienummer'},
        'Dx Geslacht': {'column': 'Geslacht'},
        'Dx Geboortejaar': {'column': 'Geboortejaar'},
        'Dx meet ID': {'column': 'Stof_meet_id'},
        'Dx Stoftest code': {'column': 'Stoftestcode'},
        'Dx Stoftest omschrijving': {'column': 'Stoftestomschrijving'},
        'Dx Helix indicatie': {'column': 'Onderzoeksindicatie'},
        'Dx Onderzoeksreden': {'column': 'Onderzoeksreden'},
        'Dx Protocolcode': {'column': 'Protocolcode'},
        'Dx Protocolomschrijving': {'column': 'Protocolomschrijving'},
    }
    header = input_file.readline().rstrip().split(',')  # expect header on first line
    for udf in udf_column:
        udf_column[udf]['index'] = header.index(udf_column[udf]['column'])

    # Parse samples
    for line in input_file:
        data = line.rstrip().replace('"', '').split(',')
        sample_name = data[header.index('Monsternummer')]

        udf_data = {}
        for udf in udf_column:
            # Transform specific udf
            if udf in ['Dx Overleden', 'Dx Spoed', 'Dx NICU Spoed']:
                udf_data[udf] = utils.letter_to_bool(data[udf_column[udf]['index']])
            elif udf in ['Dx Geslacht', 'Dx Foetus geslacht']:
                udf_data[udf] = utils.transform_sex(data[udf_column[udf]['index']])
            elif udf == 'Dx Foetus':
                udf_data[udf] = utils.foetus_to_bool(data[udf_column[udf]['index']])
            else:
                udf_data[udf] = data[udf_column[udf]['index']]

        # Set 'Dx Handmatig' udf
        if udf_data['Dx Foetus'] or udf_data['Dx Overleden'] or udf_data['Dx Spoed'] or udf_data['Dx NICU Spoed'] or udf_data['Dx Materiaal type'] != 'BL':
            udf_data['Dx Handmatig'] = True
        else:
            udf_data['Dx Handmatig'] = False

        # Set 'Dx Familie status' udf
        if udf_data['Dx Onderzoeksreden'] == 'Bevestiging diagnose':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Informativiteitstest':
            udf_data['Dx Familie status'] = 'Ouder'

        sample_list = lims.get_samples(name=sample_name)
        if sample_list:
            sample = sample_list[0]
            if udf_data['Dx Stoftest code'] in sample.udf['Dx Stoftest code']:
                print "ERROR: Duplicate sample and Stoftest code: {sample_name} - {stoftestcode}.".format(sample_name=sample_name, stoftestcode=udf_data['Dx Stoftest code'])
            else:
                print "Duplicate sample, new workflow."
                # Add existing sample to new workflow
                # Append udf fields
        else:
            container = Container.create(lims, type=container_type)
            sample = Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)
            workflow = utils.stofcode_to_workflow(lims, udf_data['Dx Stoftest code'])
            lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)

        print sample_name, udf_data
