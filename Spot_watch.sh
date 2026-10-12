#!/bin/bash
# Upload the sweep's results to S3 as soon as AWS announces a spot interruption
# (AWS gives about 2 minutes' notice). Run it next to run_parallel.py, e.g. in a
# second tmux window:
#     bash spot_watch.sh ~/Slot-Math-Optimization-GA s3://sim-result-030777446278-us-east-1-an/sweep1
PROJECT="${1:-$HOME/Slot-Math-Optimization-GA}"
DEST="${2:-s3://sim-result-030777446278-us-east-1-an/sweep1}"
cd "$PROJECT" || exit 1
echo "$(date) watching for a spot interruption notice; will sync Parallel/ to $DEST/Parallel"

while true; do
  TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
          -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-aws-ec2-metadata-token: $TOKEN" \
          http://169.254.169.254/latest/meta-data/spot/instance-action)
  if [ "$CODE" = "200" ]; then
    echo "$(date) interruption notice - uploading results"
    .venv/bin/python - "$DEST" <<'PY'
import os, sys, boto3
dest = sys.argv[1][5:]
bucket, _, prefix = dest.partition("/")
s3 = boto3.client("s3")
for root, dirs, files in os.walk("Parallel"):
    dirs[:] = [d for d in dirs if d != "TempParents"]
    for f in files:
        path = os.path.join(root, f)
        s3.upload_file(path, bucket, f"{prefix.strip('/')}/{path}".lstrip("/"))
print("uploaded")
PY
    exit 0
  fi
  sleep 5
done