#!/bin/bash

branch=${1-"master"}

# Remove everything from the repo
git rm -rf .
# Except don't remove this script
git checkout HEAD $0
git commit -m "Removed old docs"
git checkout ${branch}
git pull
cd docs
make html
cp -r _build/html ..
git checkout .
cd ..
git checkout gh-pages
mv html/* .
rm -rf html
git add .
git commit -m "Added new docs (built from ${branch})"

# Prepare the files for github...
for fl in `find . -name "*.html"` `find . -name "*.txt"` `find . -name "*.svg"` `find . -name "*.js"` `find . -name "*.css"`
do
  echo "Processing $fl"
  mv $fl $fl.old
  sed 's/_images/images/g' $fl.old > $fl
  mv $fl $fl.old
  sed 's/_modules/modules/g' $fl.old > $fl
  mv $fl $fl.old
  sed 's/_static/static/g' $fl.old > $fl
  mv $fl $fl.old
  sed 's/_sources/sources/g' $fl.old > $fl
  rm -f $fl.old
done
git mv _images images
git mv _modules modules
git mv _sources sources
git mv _static static

git add -u .

git commit -m "Prepared html files for output on github pages, which doesn't allow directories that begin with underscores."

git push origin gh-pages
