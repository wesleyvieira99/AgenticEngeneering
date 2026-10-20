variable "region" { default = "us-east-1" }
variable "name" { default = "atlas" }
variable "vpc_id" { type = string }
variable "private_subnet_ids" {
  type = list(string)
  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "Use duas subnets privadas em zonas distintas."
  }
}
variable "client_cidr" { type = string }
variable "certificate_arn" { type = string }
variable "api_image" {
  type = string
  validation {
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.api_image))
    error_message = "Use imagem de ECR fixada por digest SHA256."
  }
}
variable "config_secret_arn" {
  type        = string
  description = "Secret existente com DATABASE_URL, ATLAS_TOKEN_SECRET e ATLAS_DEMO_PASSWORD; nunca valores no tfvars."
}
variable "bedrock_model_id" { default = "amazon.nova-micro-v1:0" }
variable "price_version" {
  type = string
  validation {
    condition     = length(var.price_version) > 5 && !strcontains(upper(var.price_version), "REPLACE")
    error_message = "Informe versão real da tabela de preços aprovada."
  }
}
variable "input_usd_per_million" {
  type = number
  validation {
    condition     = var.input_usd_per_million > 0
    error_message = "Bedrock pago exige preço de entrada positivo aprovado."
  }
}
variable "output_usd_per_million" {
  type = number
  validation {
    condition     = var.output_usd_per_million > 0
    error_message = "Bedrock pago exige preço de saída positivo aprovado."
  }
}
variable "cors_origins" { type = string }
variable "database_security_group_id" {
  type        = string
  description = "Security group do RDS PostgreSQL16 pgvector existente; aplicação não cria banco público."
}
