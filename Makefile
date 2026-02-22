test:
	pytest -q

bench:
	python -m arena.cli --preset baseline-6

snapshot:
	python -m arena.cli --preset baseline-6 --markdown-out snapshots/baseline-6-seed42.md

bench-full:
	python -m arena.cli --preset full-7

snapshot-full:
	python -m arena.cli --preset full-7 --markdown-out snapshots/full-7-seed42.md
