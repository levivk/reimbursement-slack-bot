#!/usr/bin/env bash

root_dir=$(dirname $(readlink -f "${BASH_SOURCE}"))
docker build --tag reimbursement-bot .  \
    || exit

docker kill reimbursement-bot-1
docker rm reimbursement-bot-1
docker run -itd --env-file "$root_dir/keys.env" -p 8082:3000 -v /opt/reimbursement-bot-data:/app/data --log-driver journald --restart unless-stopped --name reimbursement-bot-1 reimbursement-bot
