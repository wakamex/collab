test:
	pytest -q

bench:
	python -m arena.cli --preset baseline-6

snapshot:
	python -m arena.cli --preset baseline-6 --markdown-out snapshots/baseline-6-seed42.md
