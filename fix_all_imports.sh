#!/bin/bash
# Fix all missing imports in the codebase

echo "Scanning for files with missing imports..."

# Find all JSX files that use hooks but don't import from React
find multi-agent-dashboard/src -name "*.jsx" -o -name "*.js" | while read file; do
  # Check if file uses hooks but doesn't import React
  if grep -q "useState\|useEffect\|useContext\|useReducer\|useCallback\|useMemo\|useRef" "$file"; then
    if ! head -20 "$file" | grep -q "from 'react'"; then
      echo "Fixing: $file"
      # Add React import at the top
      sed -i "1i import { useState, useEffect } from 'react';" "$file"
    fi
  fi
  
  # Check if file uses useNavigate but doesn't import it
  if grep -q "useNavigate()" "$file"; then
    if ! head -20 "$file" | grep -q "useNavigate.*from.*react-router"; then
      echo "Fixing router imports: $file"
    fi
  fi
done

echo "Done!"
