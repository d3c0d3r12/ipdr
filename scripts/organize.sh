#!/bin/zsh
set -e
BASE="/Users/d3c0d3r/Downloads/IPDR TRACKING"
cd "$BASE"

echo "==== STEP 1: Create directories ===="
mkdir -p scripts/bypass scripts/test scripts/utils scripts/windows
mkdir -p data/templates data/results data/cookies
mkdir -p assets

echo "==== STEP 2: Move Python bypass scripts ===="
for f in cloudflare_bypass_standalone.py custom_cloudflare_bypass.py; do
  [ -f "$f" ] && mv "$f" scripts/bypass/ && echo "  moved $f"
done

echo "==== STEP 3: Move Python test/lookup scripts ===="
for f in test_all_features.py test_bypass_auto.py test_cloudflare_bypass.py \
         test_infobyip_bypass.py quick_test_direct.py verify_results.py direct_ip_lookup.py; do
  [ -f "$f" ] && mv "$f" scripts/test/ && echo "  moved $f"
done

echo "==== STEP 4: Move Python utility scripts ===="
for f in extract_ip_letter.py extract_templates.py generate_password_hash.py read_templates.py; do
  [ -f "$f" ] && mv "$f" scripts/utils/ && echo "  moved $f"
done

echo "==== STEP 5: Move SQL files -> database/ ===="
for f in COMPLETE_DATABASE_FIX.sql CREATE_TABLES.sql FIX_DATABASE_NEON.sql; do
  [ -f "$f" ] && mv "$f" database/ && echo "  moved $f"
done

echo "==== STEP 6: Move Windows scripts (bat/ps1) -> scripts/windows/ ===="
for f in AUTO-INSTALL.bat INSTALL.bat SMART-START.bat START.bat STOP.bat \
         install_all.bat setup.bat start-servers.bat stop-servers.bat test_download.bat \
         deploy.ps1 deploy_fix.ps1 push_to_github.ps1 verify_security.ps1; do
  [ -f "$f" ] && mv "$f" scripts/windows/ && echo "  moved $f"
done

echo "==== STEP 7: Move data/template files -> data/ ===="
for f in airtel_template_extracted.txt ip_letter_extracted.txt jio_template_extracted.txt; do
  [ -f "$f" ] && mv "$f" data/templates/ && echo "  moved $f"
done
for f in ip_lookup_results.csv ip_lookup_results.json; do
  [ -f "$f" ] && mv "$f" data/results/ && echo "  moved $f"
done
for f in infobyip_test_cookies.json unlimited_lookup_cookies.json; do
  [ -f "$f" ] && mv "$f" data/cookies/ && echo "  moved $f"
done

echo "==== STEP 8: Move assets (images) -> assets/ ===="
for f in "Delhi_Police_Logo-1.png" "wallpaperflare.com_wallpaper.jpg" cloudflare_bypass_result.png; do
  [ -f "$f" ] && mv "$f" assets/ && echo "  moved $f"
done

echo "==== STEP 9: Delete debug/temp HTML files ===="
for f in cloudflare_bypass_result.html infobyip_8.8.8.8.html infobyip_bulk_lookup.html \
         infobyip_bulk_lookup.png test_direct_8.8.8.8.html \
         bharatkumarumma.SubscriberInfo.html privatelimitedsonaprodeveloper.SubscriberInfo.html \
         debug_infobyip_response.html debug_page.html; do
  [ -f "$f" ] && rm "$f" && echo "  deleted $f"
done

echo "==== STEP 10: Delete temp work directories ===="
for d in work-2uiWIO work-4gC8Av work-CANhew work-jXkPzq work-qbwqAB; do
  [ -d "$d" ] && rm -rf "$d" && echo "  deleted dir $d"
done

echo "==== STEP 11: Delete __pycache__ at root ===="
[ -d __pycache__ ] && rm -rf __pycache__ && echo "  deleted __pycache__"

echo "==== STEP 12: Clean up docs/archive (now empty) ===="
rmdir docs/archive 2>/dev/null && echo "  removed empty docs/archive" || true

echo ""
echo "✅ Done! Final structure:"
ls -1
