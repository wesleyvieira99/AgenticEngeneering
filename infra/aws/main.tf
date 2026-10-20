data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_vpc" "selected" { id = var.vpc_id }
locals {
  model_arn = "arn:${data.aws_partition.current.partition}:bedrock:${var.region}::foundation-model/${var.bedrock_model_id}"
}
resource "aws_cloudwatch_log_group" "atlas" {
  name              = "/atlas/${var.name}"
  retention_in_days = 14
}
resource "aws_ecs_cluster" "atlas" {
  name = var.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
resource "aws_security_group" "alb" {
  name_prefix = "${var.name}-alb-"
  vpc_id      = var.vpc_id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.client_cidr]
  }
  egress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }
}
resource "aws_security_group" "tasks" {
  name_prefix = "${var.name}-tasks-"
  vpc_id      = var.vpc_id
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.database_security_group_id]
  }
}
resource "aws_vpc_security_group_ingress_rule" "database" {
  security_group_id            = var.database_security_group_id
  referenced_security_group_id = aws_security_group.tasks.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}
resource "aws_iam_role" "execution" {
  name_prefix        = "${var.name}-execution-"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }] })
}
resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "secrets" {
  role   = aws_iam_role.execution.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = var.config_secret_arn }] })
}
resource "aws_iam_role" "runtime" {
  name_prefix        = "${var.name}-runtime-"
  assume_role_policy = aws_iam_role.execution.assume_role_policy
}
resource "aws_iam_role_policy" "model" {
  role   = aws_iam_role.runtime.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"], Resource = local.model_arn }] })
}
resource "aws_lb" "api" {
  name                       = var.name
  internal                   = true
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb.id]
  subnets                    = var.private_subnet_ids
  drop_invalid_header_fields = true
}
resource "aws_lb_target_group" "api" {
  name        = var.name
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id
  health_check {
    path    = "/api/health"
    matcher = "200"
  }
}
resource "aws_lb_listener" "tls" {
  load_balancer_arn = aws_lb.api.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}
resource "aws_ecs_task_definition" "atlas" {
  for_each                 = toset(["api", "worker"])
  family                   = "${var.name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.runtime.arn
  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }
  container_definitions = jsonencode([{
    name         = each.key, image = var.api_image, essential = true,
    user         = "10001", readonlyRootFilesystem = true,
    command      = each.key == "api" ? ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"] : ["python", "-m", "services.worker.main"],
    portMappings = each.key == "api" ? [{ containerPort = 8000, protocol = "tcp" }] : [],
    environment = [
      { name = "ATLAS_ENV", value = "production" },
      { name = "ATLAS_MODE", value = "bedrock" }, { name = "AWS_REGION", value = var.region },
      { name = "ATLAS_MODEL", value = var.bedrock_model_id },
      { name = "ATLAS_PRICE_VERSION", value = var.price_version },
      { name = "ATLAS_INPUT_USD_PER_MILLION", value = tostring(var.input_usd_per_million) },
      { name = "ATLAS_OUTPUT_USD_PER_MILLION", value = tostring(var.output_usd_per_million) },
      { name = "ATLAS_CORS_ORIGINS", value = var.cors_origins }
    ],
    secrets          = [for key in ["DATABASE_URL", "ATLAS_TOKEN_SECRET", "ATLAS_DEMO_PASSWORD"] : { name = key, valueFrom = "${var.config_secret_arn}:${key}::" }],
    logConfiguration = { logDriver = "awslogs", options = { "awslogs-group" = aws_cloudwatch_log_group.atlas.name, "awslogs-region" = var.region, "awslogs-stream-prefix" = each.key } }
  }])
}
resource "aws_ecs_service" "api" {
  name            = "${var.name}-api"
  cluster         = aws_ecs_cluster.atlas.id
  task_definition = aws_ecs_task_definition.atlas["api"].arn
  desired_count   = 1
  launch_type     = "FARGATE"
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
  depends_on = [aws_lb_listener.tls]
}
resource "aws_ecs_service" "worker" {
  name            = "${var.name}-worker"
  cluster         = aws_ecs_cluster.atlas.id
  task_definition = aws_ecs_task_definition.atlas["worker"].arn
  desired_count   = 1
  launch_type     = "FARGATE"
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }
}
output "internal_api_dns" { value = aws_lb.api.dns_name }
