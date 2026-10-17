# The film

A 1 minute 45 second narrated film about what the tracker actually finds:
`asteroids_passing_earth.mp4`.

Every number on screen comes from `public/data.json`, which `export_data.py`
writes from a live NeoWs query. Nothing is typed in by hand.

```bash
NASA_API_KEY=... python3 export_data.py   # a year of close approaches -> public/data.json
npm install
npm run sound                             # voiceover, then the music mixed under it
npm run render
```

| | |
|---|---|
| `export_data.py` | pulls the data the film puts on screen |
| `src/Film.jsx` | the eight scenes |
| `vo/lines.txt` | the narration, one line per scene |
| `voiceover.py` | reads it with Piper, an offline neural voice |
| `soundtrack.py` | synthesizes the music in numpy and ducks it under the voice |

The voice needs `pip install piper-tts` and the `en_US-ryan-high` voice from
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) in `voice/`.
The music is generated from sines and filtered noise, so there are no samples
and nothing to license.

Scene timings live in `SCENES` at the bottom of `src/Film.jsx`, and the
`VO_START` list in `soundtrack.py` has to match them. Generate the voice first,
check each line fits its scene, then render.
