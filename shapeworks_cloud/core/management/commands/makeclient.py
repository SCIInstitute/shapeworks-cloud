from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from oauth2_provider.models import Application

DEFAULT_REDIRECT_URI = 'http://localhost:8081/'


class Command(BaseCommand):
    help = 'Creates a client Application object for authentication purposes.'

    def add_arguments(self, parser):
        parser.add_argument('-u', '--uri', type=str)

    def handle(self, uri, **options):
        if not uri:
            uri = DEFAULT_REDIRECT_URI

        site = Site.objects.get_current()
        site.domain = 'app.shapeworks-cloud.org'
        site.name = 'ShapeWorks Cloud'
        site.save()

        try:
            user = User.objects.first()
            if Application.objects.filter(user=user).exists():
                raise CommandError(
                    'The client already exists. You can administer it from the admin console.'
                )
            application = Application(
                name='client-app',
                client_secret='',
                client_type='public',
                redirect_uris=uri,
                authorization_grant_type='authorization-code',
                user=user,
                skip_authorization=True,
            )
            application.save()

            with open('/client/dev/yarn.env', 'w') as f:
                f.write(f'VUE_APP_OAUTH_CLIENT_ID={application.client_id}')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Restart docker containers to complete change. \
                        Client will be available at {uri}.'
                )
            )
        except User.DoesNotExist:
            raise CommandError(
                'A user must exist before creating a client. Use createsuperuser command.'
            )
