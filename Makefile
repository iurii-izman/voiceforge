.PHONY: bootstrap verify smoke release-check cli-contract db-migrations e2e-smoke doctor toolchain security governance milestone

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

doctor:
	./scripts/doctor.sh

toolchain:
	./scripts/check_toolchain.sh

security:
	uv run pip-audit --desc --ignore-vuln CVE-2025-69872
	uv run bandit -r src -ll -q --configfile .bandit.yaml

governance:
	./scripts/apply_main_ruleset.sh

milestone:
	./scripts/create_alpha_milestone_issues.sh
