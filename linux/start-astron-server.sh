#!/bin/sh
cd ../astron/linux

# This assumes that your astrond build is located in the
# "astron/linux" directory.
./astrond --loglevel info ../config/astrond.yml
