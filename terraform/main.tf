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
}

provider "heroku" {}

data "aws_route53_zone" "shapeworks_cloud" {
  name = "app.shapeworks-cloud.org"
}
