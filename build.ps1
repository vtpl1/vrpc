$PB_REL="https://github.com/protocolbuffers/protobuf/releases"
$PB_VER="3.17.3"

# Source file location
$SOURCE = "${PB_REL}/download/v${PB_VER}/protoc-${PB_VER}-win64.zip"
# Destination to save the file
$DESTINATION = "./protoc-${PB_VER}-win64.zip"
#Download the file
Invoke-WebRequest -Uri $SOURCE -OutFile $DESTINATION

Expand-Archive -Path "./protoc-${PB_VER}-win64.zip" -DestinationPath "./protoc/" -Verbose