#!/usr/bin/env bash
# Install complete upstream skill directories, including references and assets.
# Run from a terminal with GitHub access and write access to the skills directory.
set -euo pipefail

skill_home="${CODEX_HOME:-$HOME/.codex}"
installer="${skill_home}/skills/.system/skill-installer/scripts/install-skill-from-github.py"
destination="${PPT_SKILLS_DEST:-${skill_home}/skills}"
python_bin="${PYTHON_BIN:-python3}"

if [[ ! -f "$installer" ]]; then
  printf 'Codex skill installer not found: %s\n' "$installer" >&2
  exit 1
fi

install_one() {
  local skill_name="$1" repository="$2" skill_path="$3" branch="$4"
  if [[ -d "${destination}/${skill_name}" ]]; then
    printf '[SKIP] %s already exists at %s; leaving it unchanged.\n' "$skill_name" "${destination}/${skill_name}"
    return 0
  fi
  printf '[INSTALL] %s from https://github.com/%s\n' "$skill_name" "$repository"
  "$python_bin" "$installer" --repo "$repository" --path "$skill_path" \
    --ref "$branch" --name "$skill_name" --dest "$destination"
}

# These four downloads are independent; install concurrently.
pids=()
names=(ppt-master guizang-ppt-skill frontend-slides huashu-design)
install_one ppt-master hugohe3/ppt-master skills/ppt-master main &
pids+=("$!")
install_one guizang-ppt-skill op7418/guizang-ppt-skill . main &
pids+=("$!")
install_one frontend-slides zarazhangrui/frontend-slides . main &
pids+=("$!")
install_one huashu-design alchaincyf/huashu-design . master &
pids+=("$!")

failed=0
for i in "${!pids[@]}"; do
  if ! wait "${pids[$i]}"; then
    printf '[FAILED] %s\n' "${names[$i]}" >&2
    failed=1
  fi
done
if [[ "$failed" -ne 0 ]]; then
  printf 'Some installations failed; inspect the errors above.\n' >&2
  exit 1
fi

for skill_name in "${names[@]}"; do
  if [[ ! -f "${destination}/${skill_name}/SKILL.md" ]]; then
    printf '[FAILED] SKILL.md missing: %s\n' "$skill_name" >&2
    exit 1
  fi
done
printf '\nComplete skill packages installed into %s. Available on your next turn.\n' "$destination"
