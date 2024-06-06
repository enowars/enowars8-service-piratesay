#!/bin/bash
find /data -type f -mmin +15 -exec rm {} \;