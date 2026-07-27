.PHONY: test validate generate run run-weak publish ci

test:
	python -m pytest -q

validate:
	python -m grounded_bench validate --dataset dataset/grounded-bench-v0.jsonl

generate:
	python dataset/generate_v0.py --out dataset/grounded-bench-v0.jsonl --seed 42 --count 1000

run:
	python -m grounded_bench run --dataset dataset/grounded-bench-v0.jsonl --predictions predictions/oracle.jsonl --system oracle --seed 42 --write results/oracle.json

run-weak:
	python -m grounded_bench run --dataset dataset/grounded-bench-v0.jsonl --predictions predictions/weak-baseline.jsonl --system weak-baseline --seed 42 --write results/weak.json

publish:
	python -m grounded_bench publish --results results/oracle.json --out leaderboard/
	python -m grounded_bench publish --results results/weak.json --out leaderboard/

ci: test validate run run-weak publish
