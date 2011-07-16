#!/bin/sh

# Cleans a Mercurial working copy by removing all the ignored files
# except of the local project files. You might need to extend the
# list of project file extensions below.

# Required package: trash-cli

if ! (trash --version >/dev/null); then
    echo "Failed to invoke the trash command line utility!"
    echo "Is the trash-cli package installed?"
    exit 1
fi

# Collect ignored files
IGNORED_FILES=`hg status -in`
if [ $? -ne 0 ]; then
    echo ""
    echo "Mercurial failed to list the ignored files."
    echo ""
    echo "Are you running this script inside a Mercurial working copy?"
    exit 2
fi

# Do not remove the user specific Wing IDE project file
FILES_TO_REMOVE=`hg status -in | grep -v ".wpu"`

# Is the working copy clean?
if [ -z "$FILES_TO_REMOVE" ]; then
    echo "Your working copy is already clean."
    exit 0
fi

# Trash them
echo "Trashing the following files from your working copy:"
for FN in $FILES_TO_REMOVE; do
    echo "$FN"
done
trash $FILES_TO_REMOVE
echo "Done."
