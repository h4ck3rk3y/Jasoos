#usr/bin/bash

killall -9 'twistd'
rq empty
rq suspend
