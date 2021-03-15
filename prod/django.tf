data "heroku_team" "heroku" {
  # This must be created by hand in the Heroku console
  name = "kitware"
}

data "local_file" "ssh_public_key" {
  # This must be an existing file on the local filesystem
  filename = "/home/brian/.ssh/id_rsa.pub"
}

module "django" {
  source  = "girder/django/heroku"
  version = "0.9.0"

  project_slug     = "shapeworks-cloud"
  route53_zone_id  = data.aws_route53_zone.domain.zone_id
  heroku_team_name = data.heroku_team.heroku.name
  subdomain_name   = "app"

  heroku_postgresql_plan      = "hobby-basic"
  heroku_worker_dyno_quantity = 0

  ec2_worker_instance_quantity = 1
  ec2_worker_ssh_public_key    = data.local_file.ssh_public_key.content

  additional_django_vars = {
    DJANGO_SENTRY_DSN = "https://e5943c702c4347b2aa1b4a3726d243df@o267860.ingest.sentry.io/5615130"
  }
}
