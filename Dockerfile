# FOR AWS LAMBDA DEPLOYMENT
FROM public.ecr.aws/lambda/python:3.12

# Install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Copy runtime files used by the application
COPY tmp/ ${LAMBDA_TASK_ROOT}/tmp/

# Lambda handler
CMD ["src.lambda_handler.handler"]