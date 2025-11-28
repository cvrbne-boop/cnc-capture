#!/usr/bin/env bash
if [ -f .env ]; then
  echo ".env exists"
else
  cp .env.example .env
  echo "Copied .env.example -> .env. Edit it as needed."
fi
