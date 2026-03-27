# Bootstrap — Run Once Before `terraform init`

## Create the Terraform state bucket

```bash
aws s3api create-bucket \
  --bucket ironlog-terraform-state \
  --region eu-west-3 \
  --create-bucket-configuration LocationConstraint=eu-west-3

aws s3api put-bucket-versioning \
  --bucket ironlog-terraform-state \
  --versioning-configuration Status=Enabled
```

## Then initialise Terraform

```bash
cd ../
terraform init
```
