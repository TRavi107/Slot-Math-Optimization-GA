#!/bin/bash
# Set up a fresh Ubuntu 24.04 spot instance for the slot-math GA sweep.
#
# Usage (on the instance, after copying or cloning the project):
#     bash setup_spot.sh ~/Slot-Math-Optimization-GA sim-result-030777446278-us-east-1-an
#     (arguments: project folder, S3 bucket for the results)
#
# Installs the build tools, builds the simulator (Release, tuned for this CPU),
# creates a Python venv with the optimizer's packages and checks S3 access.
set -euo pipefail

PROJECT="${1:-$HOME/Slot-Math-Optimization-GA}"
BUCKET="${2:-sim-result-030777446278-us-east-1-an}"
cd "$PROJECT"

echo "== system packages"
sudo apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q \
    build-essential cmake python3-venv python3-pip git tmux unzip
command -v aws >/dev/null || sudo snap install aws-cli --classic   # Ubuntu AMIs ship without it

echo "== build the simulator (Release, -march=native)"
rm -rf build
cmake -S Simulator -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-march=native"
cmake --build build -j "$(nproc)"

echo "== python packages (venv: $PROJECT/.venv)"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r Requirements.txt boto3
.venv/bin/pip freeze > requirements-lock.txt     # exact versions used for this sweep

echo "== simulator check (10M spins, 10 threads; sessions mode must be supported)"
SIM_THREADS=10 ./build/simulator 10000000 Simulator/src/reelset.json true /tmp/simcheck.json 1 | grep -E "Seed|Time"
./build/simulator 1000 Simulator/src/reelset.json sessions /tmp/simcheck2.json 1 80 | grep -E "Mode"

echo "== S3 check (bucket $BUCKET)"
BUCKET="$BUCKET" .venv/bin/python -c '
import os, boto3
bucket = os.environ["BUCKET"]
try:
    s3 = boto3.client("s3")
    s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
    s3.put_object(Bucket=bucket, Key="setup-check.txt", Body=b"ok")
    print(f"S3 access OK (list + write): {bucket}")
except Exception as e:
    print(f"S3 access FAILED for {bucket}: is the SimResultsProfile IAM role attached, "
          f"and does its policy name this bucket?\n  {e}")
'

cat <<EOF

Setup done. Start the sweep inside tmux so it survives SSH disconnects:
    tmux new -s sweep
    cd $PROJECT && source .venv/bin/activate
    python Optimizer/run_parallel.py pull   GA-config.yaml --runs 1-30 --s3 s3://$BUCKET/sweep1
    python Optimizer/run_parallel.py launch GA-config.yaml --runs 1-30 --workers 6 --threads 10 --s3 s3://$BUCKET/sweep1
Detach with Ctrl-b d, re-attach later with: tmux attach -t sweep
EOF