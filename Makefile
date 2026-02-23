test:
	pytest -q

bench:
	python -m arena.cli --preset baseline-6

snapshot:
	python -m arena.cli --preset baseline-6 --markdown-out snapshots/baseline-6-seed42.md

bench-full:
	python -m arena.cli --preset full-8

snapshot-full:
	python -m arena.cli --preset full-8 --markdown-out snapshots/full-8-seed42.md
