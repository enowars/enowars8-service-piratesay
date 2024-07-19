#!/bin/bash
find /data -type f -mmin +10 -exec rm {} \;