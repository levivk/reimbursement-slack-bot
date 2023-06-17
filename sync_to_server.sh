#!/bin/bash
rsync -avz --exclude=__pycache__ run_docker.sh Dockerfile keys.env requirements.txt oracle-vm:/home/ubuntu/reimbursement-bot/
