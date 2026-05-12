terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- IAM ---

resource "aws_iam_role" "lambda_exec" {
  name = "${var.function_name}-${var.environment}-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda ---

resource "aws_lambda_function" "triage" {
  function_name = "${var.function_name}-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "python3.11"
  handler       = "api.main.handler"
  filename      = "placeholder.zip"
}

# --- API Gateway ---

resource "aws_api_gateway_rest_api" "triage" {
  name        = "${var.function_name}-${var.environment}"
  description = "Public-facing API for the claims triage Lambda"
}

resource "aws_api_gateway_resource" "triage" {
  rest_api_id = aws_api_gateway_rest_api.triage.id
  parent_id   = aws_api_gateway_rest_api.triage.root_resource_id
  path_part   = "triage"
}

resource "aws_api_gateway_method" "triage_post" {
  rest_api_id   = aws_api_gateway_rest_api.triage.id
  resource_id   = aws_api_gateway_resource.triage.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "triage_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.triage.id
  resource_id             = aws_api_gateway_resource.triage.id
  http_method             = aws_api_gateway_method.triage_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.triage.invoke_arn
}

resource "aws_lambda_permission" "apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.triage.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.triage.execution_arn}/*/*"
}
