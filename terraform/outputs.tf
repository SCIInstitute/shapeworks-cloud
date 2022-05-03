output "ec2_worker_hostnames" {
  value = module.django.ec2_worker_hostnames
}

output "all_django_vars" {
  value     = module.django.all_django_vars
  sensitive = true
}
