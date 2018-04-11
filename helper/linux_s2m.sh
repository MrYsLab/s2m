#!/bin/sh

# python path
USER_BASE=$( python -m site | grep USER_BASE | grep -oP "(?<=')[^']+(?=')" )
USER_SITE=$( python -m site | grep USER_SITE | grep -oP "(?<=')[^']+(?=')" )

s2m="${USER_BASE}/bin/s2m"
uflash="${USER_BASE}/bin/uflash"
s2m_mb="${USER_SITE}/s2m/micro_bit_scripts/s2mb_min.py"
s2m_base="${USER_SITE}/s2m"

# install and upload firmware
if [ ! -f "$s2m" ]; then
	pip install --user --upgrade s2m
	pip install --user --upgrade uflash
	${uflash} "${s2m_mb}"
fi

# scratch2 path
if [ -f "/usr/bin/scratch2" ]; then
	scratch2="/usr/bin/scratch2"
fi

if [ -f "/usr/local/bin/scratch2" ]; then
	scratch2="/usr/local/bin/scratch2"
fi

if [ -f "/opt/Scratch 2/bin/Scratch 2" ]; then
	scratch2="/opt/Scratch 2/bin/Scratch 2"
fi

# launch s2m
${s2m} -b "${s2m_base}" -s "${scratch2}"
