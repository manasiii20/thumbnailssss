# System map thumbnail

480 × 463, built at 2x (960 × 926). The five subsystems from the gigamap, rearranged 2–1–2, with the isometric stepping tiles and the connections between them. The data, insights and stakeholder mapping are left out.

| Position | Subsystem |
| --- | --- |
| Top left | Communication System |
| Top right | User Behaviour |
| Centre | Spatial Dynamics |
| Bottom left | Material Flow |
| Bottom right | Environmental Impact |

## Stepping tiles

The tiles follow the gigamap's paths: Communication → Spatial Dynamics, and Spatial Dynamics (the counter) → User Behaviour.

## Connections

Line colours follow the gigamap:
- **Black:** information and material links.
- **Green:** balancing loops.
- **Blue:** reinforcing loops.
- **Orange:** impact.

| From | To | Colour | In the gigamap |
| --- | --- | --- | --- |
| Communication | Material Flow | Black | Wholesaler, supplier |
| Communication | User Behaviour | Black | Faculty ⇄ students, WhatsApp group |
| Material Flow | Spatial Dynamics | Green | Balancing loop: procurement → lack of organisation |
| Spatial Dynamics | Material Flow | Blue | Reinforcing loop: jugaad, inefficient display → storage |
| Spatial Dynamics | User Behaviour | Blue | Reinforcing loop: overcrowding → delay |
| Spatial Dynamics | Environmental Impact | Black | Lack of maintenance → cleanliness, damage |
| User Behaviour | Environmental Impact | Green | Unused items |
| Material Flow | Environmental Impact | Orange | Wastage |

Every connection is a list of isometric moves in `LINKS` in `index.html`, so a travelling highlight can follow each path later.

## Files

- `source/gigamap.webp`: the original gigamap.
- `extract.py`: cuts the five illustrations out of the gigamap, unchanged. It removes the page grey around them and the map lines that crossed their floors. Output goes to `assets/`.
- `embed.py`: packs the assets so `index.html` opens straight from disk.
- `exports/system-map@2x.png` / `system-map.png`: the still frame.
