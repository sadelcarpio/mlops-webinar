#!/usr/bin/env bash
# Borra TODO lo que creó deploy.sh (incluidos los datos en S3).
set -uo pipefail

REGION="${AWS_REGION:-us-east-1}"
CUENTA=$(aws sts get-caller-identity --query Account --output text)
NOMBRE="demanda-sein"
BUCKET="${NOMBRE}-${CUENTA}"

aws scheduler delete-schedule --name "$NOMBRE" --region "$REGION"
aws lambda delete-function --function-name "$NOMBRE" --region "$REGION"
aws ecr delete-repository --repository-name "$NOMBRE" --region "$REGION" --force >/dev/null
aws s3 rb "s3://${BUCKET}" --force
aws iam delete-role-policy --role-name "${NOMBRE}-scheduler" --policy-name invocar-lambda
aws iam delete-role --role-name "${NOMBRE}-scheduler"
aws iam delete-role-policy --role-name "${NOMBRE}-lambda" --policy-name acceso-bucket
aws iam detach-role-policy --role-name "${NOMBRE}-lambda" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name "${NOMBRE}-lambda"
echo "Listo: recursos eliminados."
