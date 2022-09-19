import getpass
from pathlib import Path

from swcc.api import swcc_session
from swcc.models import Dataset, Project

username = input('Enter username: ')
password = getpass.getpass('Enter password: ')


with swcc_session(base_url='http://localhost:8000/api/v1') as session:
    token = session.login(username, password)
    print('Authenticated with running server.')

    print('Uploading demo dataset and project.')
    dataset = Dataset(
        name='Demo Data',
        description='An example dataset',
        license='No license',
        acknowledgement='No acknowledgement',
    ).force_create()

    project_file = Path('project_demo/project_demo.swproj')
    project = Project(
        file=project_file,
        description='First project for demo data',
        dataset=dataset,
        last_cached_analysis='analysis/project_demo_analysis.json',
    ).create()

    print('Done.')
