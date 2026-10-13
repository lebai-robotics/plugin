#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

dir=$1
mkdir -p .oss

if [ ! -s $dir/plugin.json ]; then
    echo "miss plugin.json"
    exit 1
fi

status=$(curl --head "l-os.lebai.ltd/plugin/$dir.zip" 2>/dev/null | head -n 1| cut -d$' ' -f2)
if [ "$status" != "404" ]
then
    echo "更新$dir"
    #continue
else
    echo "发布$dir"
fi

cd $dir
if [ -s list.sh ]; then
    PLUGIN_CI_LIST=`bash list.sh`
else
    PLUGIN_CI_LIST=`git ls-files`
fi
zip -q -r ../.oss/$dir.zip $PLUGIN_CI_LIST
cd ../

echo "success package .oss/$dir.zip"