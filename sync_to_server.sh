#!/bin/bash
rsync -avz --exclude=__pycache__ run_docker.sh Dockerfile keys.env requirements.txt src oracle-vm:/home/ubuntu/reimbursement-bot/
