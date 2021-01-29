data "heroku_team" "heroku" {
  # This must be created by hand in the Heroku console
  name = "kitware"
}

module "django" {
  source  = "girder/django/heroku"
  version = "0.5.0"

  project_slug     = "shapeworks-cloud"
  route53_zone_id  = data.aws_route53_zone.shapeworks_cloud.zone_id
  heroku_team_name = data.heroku_team.heroku.name
  subdomain_name   = "app"

  heroku_postgresql_plan = "hobby-basic"
  heroku_worker_dyno_quantity = 0
  additional_django_vars = {
    DJANGO_SENTRY_DSN = "https://e5943c702c4347b2aa1b4a3726d243df@o267860.ingest.sentry.io/5615130"
  }
}
