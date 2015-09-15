#!/bin/bash
cd sc-*-linux && ./bin/sc -u $SAUCE_USERNAME -k $SAUCE_ACCESS_KEY --tunnel-identifier $CIRCLE_BUILD_NUM-$CIRCLE_NODE_INDEX --readyfile ~/sauce_is_ready &disown
I=0
while true; do
    if [ -e ~/sauce_is_ready ]
    then
        break;
    fi
    sleep 1
    I=$(( I + 1 ))
    if [ $(( I % 60 )) -eq 0 ]
    then
        killall --wait sc
        ./bin/sc -u $SAUCE_USERNAME -k $SAUCE_ACCESS_KEY --tunnel-identifier $CIRCLE_BUILD_NUM-$CIRCLE_NODE_INDEX --readyfile ~/sauce_is_ready &disown
    fi
done