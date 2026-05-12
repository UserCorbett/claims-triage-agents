This is a structural stub, not a deployment.

The Terraform here describes the deployment shape: AWS Lambda fronted by API Gateway, with the FastAPI app from `api/main.py` wrapped via an ASGI adapter (Mangum) in a real build. It has not been applied. There is no `placeholder.zip` in this repo.

The point is to demonstrate the deployment pattern, not to ship infrastructure. If extending to a real deployment, you would:

1. Build a deployment package (`pip install -t package/`, zip with `api/main.py` and `src/claims_triage`)
2. Add Mangum as the ASGI adapter (`from mangum import Mangum; handler = Mangum(app)`)
3. Update `lambda_function.filename` to point to the real zip
4. Add a CloudWatch log group and tighten the IAM policy
5. Add observability: X-Ray, structured log shipping, alarms on error rate and latency
