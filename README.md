### Scope
Simple container to set your current public IP to a security group

### Usage

```
docker run -it \
-e ports='[{"port": 80, "protocol": "tcp"},{"port": 3306, "protocol": "tcp"}]' \
-e AWS_ACCESS_KEY="YOUR_ACCESS_KEY" \
-e AWS_SG="sg-yourSGid" \
-e AWS_REGION="eu-west-1" \
daniego/aws_sg_setup
```
