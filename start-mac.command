#!/bin/zsh
cd -- "${0:A:h}" || exit 1
# Finder does not load interactive shell PATH; include common Python/Homebrew/nvm locations.
export PATH="/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/Current/bin:$PATH"
for candidate in "$HOME"/.nvm/versions/node/*/bin(N/); do
  if [[ -x "$candidate/node" ]] && "$candidate/node" -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then export PATH="$candidate:$PATH"; fi
done
if ! command -v python3 >/dev/null; then
  echo '请先安装 Python 3：https://www.python.org/downloads/macos/'
  read '?按回车退出'; exit 1
fi
if ! command -v node >/dev/null || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
  echo '请先安装 Node.js 22 或更新版本：https://nodejs.org/'
  read '?按回车退出'; exit 1
fi
python3 launch.py --browser
result=$?
if (( result != 0 )); then read '?启动遇到问题，按回车退出'; fi
exit $result
