# Graduation cake composite — working brief

Drop the three source photos in this folder, e.g.:
- elder.jpg   (older man, white thobe + white ghutra + black egal, full beard)
- officer.jpg (man in tan/khaki dress uniform, peaked cap, medals)
- young.jpg   (young man, red-white shemagh + black egal, white thobe)

## Locked creative direction
- Format: tall portrait (4:5), for cake print
- Styling: keep each person's real attire; add tasteful graduation accents (gold tassels/stars), do NOT force mortarboards
- Background: clean, elegant, celebratory (cream + gold)
- Faces: must be preserved from the source photos (image-to-image / multi-image)
- Text (Arabic, added as a clean overlay for legibility):
  «ألف مبروك لعموم اسرة سعد بن محمد بن حسين الدوسري على نجاح ابنائة ونجله»

## Run (once files are present)
GOOGLE_AI_API_KEY=... python3 .claude/skills/banana/scripts/composite.py \
  --aspect-ratio "4:5" --resolution "2K" \
  --image assets/graduates/elder.jpg \
  --image assets/graduates/officer.jpg \
  --image assets/graduates/young.jpg \
  --prompt "<composite prompt>"
