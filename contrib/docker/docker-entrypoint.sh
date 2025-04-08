#!/bin/sh
# vim:sw=4:ts=4:et

set -e

exec 3>&1

if [ -n "$1" ]; then
    if /usr/bin/find "/app/docker-entrypoint.d" -mindepth 1 -maxdepth 1 -type f -print -quit 2>/dev/null | read v; then
        echo >&3 "$0: /app/docker-entrypoint.d is not empty, will attempt to perform configuration"

        chmod +x /app/docker-entrypoint.d/*.sh

        echo >&3 "$0: Looking for shell scripts in /app/docker-entrypoint.d"
        find "/app/docker-entrypoint.d" -follow -type f -print | sort -V | while read -r f; do
            case "$f" in
                *.sh)
                    if [ -x "$f" ]; then
                        echo >&3 "$0: Launching $f";
                        "$f"
                    else
                        # warn on shell scripts without exec bit
                        echo >&3 "$0: Ignoring $f, not executable";
                    fi
                    ;;
                *) echo >&3 "$0: Ignoring $f";;
            esac
        done

        echo >&3 "$0: Configuration complete; ready for start up"
    else
        echo >&3 "$0: No files found in /app/docker-entrypoint.d, skipping configuration"
    fi
fi

echo "$@"

exec "$@"
