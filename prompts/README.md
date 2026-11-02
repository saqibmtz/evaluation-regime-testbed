# Prompts

| File | Stage | Source |
|---|---|---|
| `focus_intro.txt` | Focus notes: introduction and positioning | Pilot prompt (verbatim) |
| `focus_method.txt` | Focus notes: method and evidence | Reconstructed to match the pilot's structure |
| `focus_contribution.txt` | Focus notes: overall contribution | Reconstructed to match the pilot's structure |
| `persona_system.txt` | Persona reviews: shared system prompt | Pilot prompt (verbatim) |
| `persona_empiricist.txt` | Persona lens | Pilot prompt (verbatim) |
| `persona_theorist.txt` | Persona lens | Reconstructed to match the pilot's structure |
| `persona_systems_pragmatist.txt` | Persona lens | Reconstructed to match the pilot's structure |
| `persona_novelty_gatekeeper.txt` | Persona lens | Reconstructed to match the pilot's structure |
| `committee_synthesis.txt` | Area-chair synthesis | Pilot prompt (verbatim) |
| `decision_head.txt` | Decision stage | Pilot prompt (verbatim) |

The JSON output instruction for persona reviews is appended by `pipeline/committee.py`.
Persona prompts are interventions to be validated: the pilot finds that different
lenses produce highly overlapping review content.
