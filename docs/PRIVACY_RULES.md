# CounterIQ — Privacy Rules

These rules are enforced in code, dependency policy, CI, DB constraints, and
copy. Violations are build-failing.

## Permanently disabled (MVP and beyond)
1. **Facial recognition.** No face embeddings stored, no face DB, no face-match.
   Banned imports: `face_recognition`, `dlib` face APIs, `insightface`, `deepface`.
2. **Demographic detection.** No age/gender/race inference.
3. **Emotion / sentiment detection.** No facial-affect models. No body-language
   intent claims.
4. **Speech transcription.** Banned imports: `whisper`, `vosk`, `deepspeech`,
   `speech_recognition`. No keyword detection.
5. **Conversation analysis.** No NLP over speech.
6. **Voice fingerprinting / speaker identification.**
7. **Customer identity persistence across visits.** Tracks expire after 4 hours.
8. **Automatic discipline.** No automated employment decisions.
9. **Automatic accusation.** No event copy ever uses "stole/thief/guilty."
10. **Private-area monitoring.** Bathrooms, break rooms, dressing rooms, offices
    blocked at install. Documented in install playbook.

## Audio rules
- Audio OFF by default at every layer (DB, edge config, UI).
- Owner is the ONLY role that can enable.
- Per-camera toggle.
- Compliance row required (DB trigger blocks the flag flip without it).
- 5-step compliance modal: jurisdiction → legal-review ack → signage updated →
  employee notice acknowledged → "no transcription" ack → type "ENABLE AUDIO".
- Audio retention defaults 7 days, capped at video retention.
- Edge `audio_*` modules not imported unless config flag is true.
- ffmpeg audio process killed within 5s of disable.
- Speech deny-list constant in `audio_detect.py` checked even if allow-list
  misconfigured.
- No PCM persisted to disk except as a clip on event.
- Master kill switch on `/settings/privacy` flips all cameras + revokes
  `audio_policy_confirmed`.

## Always required before monitoring begins
- Customer signage at every entrance + counter.
- Written employee notice signed by every employee.
- Owner acceptance of TOS (advisory-only language).
- All clip access (any role, including CounterIQ admin) is audit-logged.

## Allowed event language
observed · possible · flagged for review · review required · unmatched ·
no matching POS transaction found · review clip · behavioral observation ·
product-loss risk · off-register transaction review · pattern flagged

## Forbidden event language (regex-blocked in sanitizer)
stole · stolen · theft · thief · thieves · guilty · caught · criminal ·
confirmed theft · employee stealing · customer stealing · said · saying ·
told · spoke · conversation · argument · fight · threat confirmed ·
admitted · confessed · demographic adjectives attached to a person reference

## Sanitizer is mandatory
LLM output passes through banned-words regex before render or send. Two
violations triggers deterministic fallback template. No exceptions.
