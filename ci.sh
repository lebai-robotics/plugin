#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

mkdir -p .oss
arr=()
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
    obj="{\"name\":\"$dir\", \"url\":\"https://l-os.lebai.ltd/plugin/${dir}.zip\"}"
    arr+=("$obj")
    cd ../
done

# 构造 JSON 数组
json="["
for ((i=0; i<${#arr[@]}; i++)); do
  json+=" ${arr[$i]}"
  if [ $i -lt $((${#arr[@]}-1)) ]; then
    json+=","
  fi
done
json+=" ]"
echo $json > .oss/info.json

cd .oss/
for file in `ls *.zip`
do
    md5sum $file | cut -d ' ' -f1 > $file.md5sum
done
cd ../

ossutil -e $AWS_ENDPOINT -i $AWS_ACCESS_KEY_ID -k $AWS_SECRET_ACCESS_KEY cp -r -f -u .oss/ oss://l-os/plugin/
