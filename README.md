<img src="web/shapeworks/public/favicon.ico" alt="ShapeWorks logo" width="100"/>

# ShapeWorks Cloud

This is a cloud based webapp alternative to a desktop application called ShapeWorks Studio, made in collaboration with ShapeWorks. See the [ShapeWorks Website](http://sciinstitute.github.io/ShapeWorks/) for more details.

## Deployed Instance

See [https://www.shapeworks-cloud.org/](https://www.shapeworks-cloud.org/).

Or, access the OpenAPI REST interface at [https://app.shapeworks-cloud.org/api/docs/swagger/](https://app.shapeworks-cloud.org/api/docs/swagger/).

For admins, visit [https://app.shapeworks-cloud.org/admin](https://app.shapeworks-cloud.org/admin).


## Quick Start
Using `docker-compose` is the simplest configuration to start with, so it is a prerequisite for this quick start.

### Initial Setup
1. Run `docker-compose run --rm django ./manage.py migrate`
1. Run `docker-compose run --rm django ./manage.py makeclient`
2. Run `docker-compose run --rm django ./manage.py createsuperuser`
   and follow the prompts to create your own user

### Example Data
The ShapeWorks Cloud Client ([SWCC](swcc)) is a Python library to interact with a ShapeWorks Cloud server. You can use SWCC to upload some example data.

1. Run `pip install swcc`

   > For developers, use `pip install -e ./swcc`

2. Run `cd swcc/examples`
3. Run `python upload_examples.py`


### Run Application
1. Run `docker-compose up`
2. Access the site, starting at http://localhost:8081/
2. Access admin console at http://localhost:8000/admin/
3. When finished, use `Ctrl+C`

### Application Maintenance
Occasionally, new package dependencies or schema changes will necessitate maintenance. To non-destructively update your development stack at any time:
1. Run `docker-compose pull`
2. Run `docker-compose build --pull --no-cache`
3. Run `docker-compose run --rm django ./manage.py migrate`
