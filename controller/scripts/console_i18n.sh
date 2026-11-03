#!/bin/bash
# UI text only; printf never evaluates message contents as shell code.
companion_message() {
  if [[ "${COMPANION_LANGUAGE:-zh-CN}" == en ]]; then printf '%s\n' "$2";
  else printf '%s\n' "$1"; fi
}
companion_prompt() {
  if [[ "${COMPANION_LANGUAGE:-zh-CN}" == en ]]; then printf '%s' "$2";
  else printf '%s' "$1"; fi
}
