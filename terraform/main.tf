terraform {
  backend "remote" {
    hostname     = "app.terraform.io"
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
  name = "shapeworks-cloud.org"
}
