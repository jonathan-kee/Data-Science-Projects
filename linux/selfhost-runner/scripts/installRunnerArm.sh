# Below Bash codes might be wrong

# Create a directory and enter it
mkdir actions-runner && cd actions-runner

# Download the latest runner package (OSX arm64 (Apple silicon))
curl -o actions-runner-linux-arm64-2.334.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.334.0/actions-runner-linux-arm64-2.334.0.tar.gz

# Optional: Validate the hash
echo "f44255bd3e80160eb25f71bc83d06ea025f6908748807a584687b3184759f7e4  actions-runner-linux-arm64-2.334.0.tar.gz" | shasum -a 256 -c

# Extract the installer
tar xzf ./actions-runner-linux-arm64-2.334.0.tar.gz

# Verify extracted files
ls -1