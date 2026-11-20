#!/usr/bin/env bash
# Despliega el job diario en AWS:
#
#   EventBridge Scheduler (6:00 am Lima) --> Lambda (imagen Docker) <--> S3 (carpeta data/)
#
# Uso: ./infra/deploy.sh          (se puede correr varias veces: actualiza lo que ya existe)
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
CUENTA=$(aws sts get-caller-identity --query Account --output text)
NOMBRE="demanda-sein"
BUCKET="${NOMBRE}-${CUENTA}"
IMAGEN="${CUENTA}.dkr.ecr.${REGION}.amazonaws.com/${NOMBRE}:latest"

echo "==> 1/5 Bucket S3 privado: ${BUCKET}"
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" >/dev/null
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
  fi
fi

echo "==> 2/5 Imagen Docker -> ECR"
aws ecr describe-repositories --repository-names "$NOMBRE" --region "$REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$NOMBRE" --region "$REGION" >/dev/null
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "${CUENTA}.dkr.ecr.${REGION}.amazonaws.com"
docker build --platform linux/amd64 --provenance=false --target produccion -t "$IMAGEN" .
docker push "$IMAGEN"

echo "==> 3/5 Rol IAM de la Lambda (logs + acceso solo a su bucket)"
if ! aws iam get-role --role-name "${NOMBRE}-lambda" >/dev/null 2>&1; then
  aws iam create-role --role-name "${NOMBRE}-lambda" >/dev/null --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
  sleep 10  # IAM tarda unos segundos en propagar un rol nuevo
fi
aws iam attach-role-policy --role-name "${NOMBRE}-lambda" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam put-role-policy --role-name "${NOMBRE}-lambda" --policy-name acceso-bucket --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {\"Effect\": \"Allow\", \"Action\": [\"s3:GetObject\", \"s3:PutObject\"], \"Resource\": \"arn:aws:s3:::${BUCKET}/*\"},
    {\"Effect\": \"Allow\", \"Action\": \"s3:ListBucket\", \"Resource\": \"arn:aws:s3:::${BUCKET}\"}]}"
ROL_LAMBDA=$(aws iam get-role --role-name "${NOMBRE}-lambda" --query Role.Arn --output text)

echo "==> 4/5 Función Lambda"
VARIABLES="Variables={S3_BUCKET=${BUCKET},MLFLOW_TRACKING_URI=}"
if aws lambda get-function --function-name "$NOMBRE" --region "$REGION" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$NOMBRE" --image-uri "$IMAGEN" --region "$REGION" >/dev/null
  aws lambda wait function-updated --function-name "$NOMBRE" --region "$REGION"
else
  aws lambda create-function --function-name "$NOMBRE" --region "$REGION" >/dev/null \
    --package-type Image --code ImageUri="$IMAGEN" --role "$ROL_LAMBDA" \
    --timeout 300 --memory-size 2048 --environment "$VARIABLES"
  aws lambda wait function-active-v2 --function-name "$NOMBRE" --region "$REGION"
fi

echo "==> 5/5 Programación diaria: 6:00 am hora de Lima"
FUNCION=$(aws lambda get-function --function-name "$NOMBRE" --region "$REGION" --query Configuration.FunctionArn --output text)
if ! aws iam get-role --role-name "${NOMBRE}-scheduler" >/dev/null 2>&1; then
  aws iam create-role --role-name "${NOMBRE}-scheduler" >/dev/null --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "scheduler.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
  sleep 10
fi
aws iam put-role-policy --role-name "${NOMBRE}-scheduler" --policy-name invocar-lambda --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{\"Effect\": \"Allow\", \"Action\": \"lambda:InvokeFunction\", \"Resource\": \"${FUNCION}\"}]}"
ROL_SCHEDULER=$(aws iam get-role --role-name "${NOMBRE}-scheduler" --query Role.Arn --output text)
PROGRAMACION=(--name "$NOMBRE" --region "$REGION" --schedule-expression "cron(0 6 * * ? *)"
  --schedule-expression-timezone America/Lima --flexible-time-window Mode=OFF
  --target "Arn=${FUNCION},RoleArn=${ROL_SCHEDULER}")
if aws scheduler get-schedule --name "$NOMBRE" --region "$REGION" >/dev/null 2>&1; then
  aws scheduler update-schedule "${PROGRAMACION[@]}" >/dev/null
else
  aws scheduler create-schedule "${PROGRAMACION[@]}" >/dev/null
fi

echo
echo "Listo. Para correr el job ahora mismo (la primera vez descarga todo el histórico, ~1 min):"
echo "  aws lambda invoke --function-name ${NOMBRE} --region ${REGION} --cli-read-timeout 310 respuesta.json && cat respuesta.json"
