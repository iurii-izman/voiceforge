.PHONY: bootstrap verify smoke release-check cli-contract db-migrations e2e-smoke test-integration eval eval-ab doctor toolchain security governance governance-check new-code-coverage coverage milestone sonar-status flatpak-build

bootstrap:
	./scripts/bootstrap.sh

verify:
	./scripts/verify_pr.sh

smoke:
	./scripts/smoke_clean_env.sh

release-check:
	./scripts/verify_pr.sh
	./scripts/smoke_clean_env.sh
	uv build --wheel

cli-contract:
	./scripts/check_cli_contract.sh

db-migrations:
	uv run pytest tests/test_db_migrations.py -q

e2e-smoke:
	uv run pytest tests/test_cli_e2e_smoke.py -q

test-integration:
	uv run pytest tests/test_stt_integration.py -v -m integration

eval:
	uv run pytest tests/eval/ -q --tb=line

# Phase D #70: A/B model comparison (requires anthropic key). Usage: make eval-ab [MODEL_A=haiku] [MODEL_B=sonnet]
eval-ab:
	MODEL_A="$(or $(MODEL_A),haiku)" MODEL_B="$(or $(MODEL_B),sonnet)" uv run python scripts/eval_ab.py

doctor:
	./scripts/doctor.sh

toolchain:
	./scripts/check_toolchain.sh

security:
	uv run pip-audit --desc --ignore-vuln CVE-2025-69872
	uv run bandit -r src -ll -q --configfile .bandit.yaml

governance:
	./scripts/apply_main_ruleset.sh

governance-check:
	./scripts/check_repo_governance.sh

new-code-coverage:
	./scripts/check_new_code_coverage.sh

# Coverage report (issue #56). Run in toolbox to avoid OOM; when ≥75%, set fail_under=75 in pyproject.toml
coverage:
	uv run pytest tests/ -q -m "not integration" --cov=src/voiceforge --cov-report=term-missing

milestone:
	./scripts/create_alpha_milestone_issues.sh

sonar-status:
	./scripts/check_sonar_status.sh

# Phase D #73: Flatpak build (desktop). Requires flatpak-builder, org.gnome.Platform//46. See docs/runbooks/offline-package.md
flatpak-build:
	./scripts/build-flatpak.sh
