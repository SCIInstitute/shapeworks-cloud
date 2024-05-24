data "heroku_team" "heroku" {
  # This must be created by hand in the Heroku console
  name = "shapeworks"
}

module "django" {
  source  = "girder/girder4/heroku"
  version = "0.10.1"

  project_slug     = "shapeworks-cloud"
  route53_zone_id  = data.aws_route53_zone.shapeworks_cloud.zone_id
  heroku_team_name = data.heroku_team.heroku.name
  subdomain_name   = "app"

  heroku_postgresql_plan      = "basic"
  heroku_worker_dyno_quantity = 0

  heroku_web_dyno_size    = "basic"
  heroku_worker_dyno_size = "basic"

  ec2_worker_instance_type     = "m4.large"
  ec2_worker_instance_quantity = 1
  ec2_worker_ssh_public_key    = var.ec2_worker_ssh_public_key
  ec2_worker_volume_size       = 40

  additional_django_vars = {
    DJANGO_API_URL               = "https://shapeworks-5f5454939472.herokuapp.com/api/v1"
    DJANGO_HOMEPAGE_REDIRECT_URL = "https://ec2-35-173-217-198.compute-1.amazonaws.com"
  }
  django_cors_origin_whitelist = ["https://ec2-35-173-217-198.compute-1.amazonaws.com"]
}

resource "aws_route53_record" "github_pages" {
  zone_id = data.aws_route53_zone.shapeworks_cloud.zone_id
  name    = "www"
  type    = "CNAME"
  ttl     = "300"
  records = ["girder.github.io."]
}
