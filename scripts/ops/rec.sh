#!/bin/bash
# rec.sh submitted KEY:JOB [KEY:JOB ...]   |   rec.sh done JOB=URL [JOB=URL ...] [--charged N applies to none]
mode=$1; shift
for x in "$@"; do
  if [ "$mode" = submitted ]; then python3 -m gudi operator submitted "${x%%:*}" "${x##*:}" | tail -1
  else python3 -m gudi operator done "${x%%=*}" "${x#*=}" | tail -1; fi
done
