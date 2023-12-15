#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

mkdir -p .oss
for dir in `ls`
do
    if [ ! -s $dir/plugin.json ]; then
        continue
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
    zip -q -r ../.oss/$dir.zip *
    cd ../
done

ossutil -e $AWS_ENDPOINT -i $AWS_ACCESS_KEY_ID -k $AWS_SECRET_ACCESS_KEY cp -f -u ./info.json oss://l-os/plugin/

cd .oss/
for file in `ls *.zip`
do
    md5sum $file | cut -d ' ' -f1 > $file.md5sum
done
cd ../

ossutil -e $AWS_ENDPOINT -i $AWS_ACCESS_KEY_ID -k $AWS_SECRET_ACCESS_KEY cp -r -f -u .oss/ oss://l-os/plugin/
