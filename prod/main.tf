terraform {
  backend "remote" {
    organization = "shapeworks-cloud"

    workspaces {
      name = "shapeworks-cloud-prod"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  # Must set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY envvars
}
provider "heroku" {
  # Must set HEROKU_EMAIL, HEROKU_API_KEY envvars
}

data "aws_route53_zone" "domain" {
  # This must be created by hand in the AWS console
  name = "shapeworks-cloud.org"
}
