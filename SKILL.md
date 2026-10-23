---
name: magic-hour
description: Generate AI video and images with the Magic Hour API (Sora 2, Veo 3.1, Kling 3.0, WAN 2.2, GPT-image, Nano Banana Pro). Text-to-video, image-to-video, image generation; free tier available.
version: 1.0.0
homepage: https://github.com/RhythmP28/clawhub-magic-hour
metadata:
  {
    "openclaw":
      {
        "emoji": "🎬",
        "requires":
          {
            "bins": ["python3"],
            "python": ["magic_hour"],
            "env": ["MAGIC_HOUR_API_KEY"],
          },
        "primaryEnv": "MAGIC_HOUR_API_KEY",
      },
  }
---

# Magic Hour

One API key for many video/image models: Sora 2, Veo 3.1, Kling 3.0, Seedance, MiniMax H3, WAN 2.2, LTX 2.3 (video) and GPT-image, Nano Banana Pro, Seedream, Flux, Z-Image (image). Jobs are async; the scripts below submit, poll every ~5s, and print a single JSON line when done.

## Data and file scope

Generation sends the authorized prompt, generation settings, and selected media to Magic Hour for remote processing. Use only inputs the user has authorized for that purpose; do not include unrelated chat history, project data, credentials, or private files. Ask before uploading only when the selected file or permission is unclear.

For image-to-video, the SDK automatically uploads the local path supplied to the script. Pass only the explicitly selected PNG, JPEG, or WebP image; never search for substitute files or upload directories. The script checks that a path exists, not that its contents are a valid image. Read `MAGIC_HOUR_API_KEY` only for Magic Hour authentication, keep it out of prompts and logs, and save downloads only in the user-selected output directory. See [Magic Hour's privacy policy](https://magichour.ai/privacy) for data handling; do not promise local-only processing or immediate deletion.

## Fastest route: hosted MCP server (zero install)

Magic Hour runs a remote MCP server at `https://mcp.magichour.ai/` (docs: https://magichour.ai/mcp). If your agent can attach MCP servers, add it with header `Authorization: Bearer $MAGIC_HOUR_API_KEY` (Claude web/desktop uses OAuth, client id `magic-hour-mcp`). It exposes image, video and audio generation tools plus upload URL allocation (`video_assets_generate_presigned_url`) and wait/status tools, so no local SDK is needed. Discover the live input schemas before calling tools; clients may prefix their names. For a local input file, request an upload URL, upload its raw bytes with an HTTPS `PUT` from a runtime that can read the file, and pass the returned `file_path` to creation. Allocating the URL does not upload the file, and the hosted server cannot read a local filesystem path. The scripts below are the fallback for agents without MCP, or when you want plain JSON from a shell.

## Setup (script route)

1. Free key (400 credits on signup + 100/day, no card): https://magichour.ai/developer
2. `export MAGIC_HOUR_API_KEY=mhk_...`
3. `pip install magic_hour==0.89.0` (official SDK, Python >= 3.10)

## Scripts

All scripts print one JSON object to stdout: `{project_id, status, model, url, urls, credits_charged, ...}` and exit non-zero with `{"status":"error","error":{...}}` on failure. Add `--download-dir DIR` to also save the file locally (`downloaded_paths` in the output). Add `--no-wait` to return immediately (`status: "queued"`) and check later with `status.py`.

```bash
# Text -> video (default: wan-2.2, 5s, 480p, 16:9 = 120 credits, free tier)
python3 {baseDir}/scripts/text_to_video.py "a corgi surfing at golden hour, slow-motion, cinematic" \
  --model wan-2.2 --duration 5 --resolution 480p --aspect-ratio 16:9 --download-dir ./out

# Image -> video (uploads the explicitly selected image to Magic Hour; public https URL also works)
python3 {baseDir}/scripts/image_to_video.py ./photo.png "slow push-in, hair moves in the wind" \
  --model kling-3.0 --duration 5 --resolution 720p

# Text -> image(s)
python3 {baseDir}/scripts/generate_image.py "isometric cozy coffee shop, soft morning light" \
  --model flux-2-klein --count 1 --aspect-ratio 1:1

# Poll a queued project
python3 {baseDir}/scripts/status.py <project_id> --kind video --wait
```

## Choosing a video model

| Model                               | Durations (s)            | Credits/sec    | Notes                                       |
| ----------------------------------- | ------------------------ | -------------- | ------------------------------------------- |
| `wan-2.2`                           | 3-10, 15                 | 24             | FREE. Default. Cheap general-purpose clips. |
| `ltx-2.3`                           | 1-10, 15, 20, 25, 30     | 24             | FREE. Longest free clips (30s).             |
| `minimax-h3`                        | 1-10, 15, 20, 25, 30     | 24             | FREE. Up to 1080p.                          |
| `seedance-1.5`                      | 4-12                     | 30             | Good value step up.                         |
| `kling-2.6`                         | 5, 10                    | 36             |                                             |
| `kling-3.0`                         | 3-15                     | 48             | Best motion/physics for the price.          |
| `veo3.1-lite`                       | 4, 6, 8, 16...56         | 48             |                                             |
| `veo3.1` / `veo3.1-audio`           | 4, 6, 8, 16...56         | 96             | Cinematic; `-audio` adds sound (`--audio`). |
| `sora-2`                            | 4, 8, 12, 24, 36, 48, 60 | 120            | Complex multi-shot scenes. 720p max.        |
| `seedance-2.0-mini` / `2.0` / `2.5` | 4-15 / 4-15 / 4-30       | 96 / 120 / 120 | 720p max.                                   |

Rules of thumb:

- Cost = credits/sec x duration (e.g. kling-3.0 5s = 240). Failed jobs are auto-refunded. Tell the user the estimated cost before spending more than ~500 credits.
- Stay on `wan-2.2` / `ltx-2.3` / `minimax-h3` unless the user asks for quality or has a paid plan; the free tier is ~100 credits/day.
- Duration must be in the model's allowed list or the API rejects the job. The scripts warn on stderr if it is not.
- Use `9:16` for shorts/reels, `16:9` for landscape, `1:1` for social tiles.
- Image-to-video: keep the prompt about motion ("camera slowly orbits", "she turns and smiles"); the image already defines the look.

## Image models

`default` (good all-rounder), `gpt-image-2` (text rendering, instructions), `nano-banana-pro` (photoreal, editing), `seedream-v5-pro`, `flux-2-klein` (fast), `z-image-turbo` (fastest), `qwen-image-2.1` (edits). Image cost varies by model, resolution, and count; check the current endpoint documentation or live MCP schema before quoting or spending credits. Do not assume 50 credits is an upper bound.

## Prompting tips

- Before generation, define the intended use, aspect ratio, resolution, duration, composition or camera motion, must-preserve details, and failure conditions. Choose the model from the live schema for the behavior that matters most; when final quality is the priority, do not default to the cheapest or fastest option.
- Video prompts: subject + action + camera move + lighting/style + mood, 1-3 sentences. Avoid listing many scenes for short clips.
- For exact identity, product geometry, packaging, logos, or branded text, use an authorized reference image and an editing or image-to-video workflow instead of recreating the subject from text alone. Tell the model what must remain unchanged.
- Rendering takes ~1-5 minutes for video, seconds for images. Output URLs expire after a while; download with `--download-dir` if the user needs the file.
- If polling times out after a project ID was returned, resume that same project with `status.py`; do not create a replacement job. If creation times out before an ID is returned, reconcile it in the dashboard before retrying: the first request may already have created a paid job. For an explicit failed project, read `error.message`, correct the cause, and only submit another generation within the user's authorized credit budget.

After download, inspect the output before calling it finished. For images, check composition, crop, anatomy, identity, requested text and logos, unintended lettering or brand-like marks, and visible artifacts. For video, also check the first and last frames, motion, temporal consistency, flicker, warping, and unwanted cuts. If a required criterion fails, state the failure and change the smallest useful input, prompt, model, or resolution within the authorized credit budget.

## References

- `{baseDir}/references/api.md` - raw HTTP endpoints, poll loop, file upload (use if the SDK is unavailable, e.g. with curl).
- `{baseDir}/references/models.md` - full model catalogue and pricing.
- Docs: https://docs.magichour.ai - Other integrations: PyPI `langchain-magic-hour`, `llama-index-tools-magic-hour`; npm `langchain-magic-hour`, `magic-hour-ai-provider`; hosted MCP https://mcp.magichour.ai/ (legacy self-hosted: github.com/magichourhq/magic-hour-mcp).
