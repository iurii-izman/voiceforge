# Rollback Runbook (alpha releases)

Use this when an alpha release is broken or incorrect.

## Trigger Conditions

1. Broken wheel/runtime after tag publication.
2. Invalid release notes or missing critical files.
3. Security issue in released artifact.

## Rollback Steps

1. Freeze rollout communication and mark release as invalid.
2. If release is still draft, delete draft and regenerate from fixed commit.
3. If release is published:
   - Create patch commit on `main`.
   - Create a new tag (do not retag existing release).
   - Publish superseding alpha tag with corrected artifacts.
4. Update `CHANGELOG.md` with rollback note and correction.
5. Capture incident note in PR/issue with root cause and prevention.

## Validation After Rollback

1. `./scripts/verify_pr.sh`
2. `./scripts/smoke_clean_env.sh`
3. Release workflow produced wheel and SBOM
4. Release notes clearly mark superseded/broken tag
