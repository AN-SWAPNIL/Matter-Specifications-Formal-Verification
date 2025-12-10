import subprocess

result = subprocess.run(
    ["wsl", "/home/linuxbrew/.linuxbrew/bin/tamarin-prover","temp_tamarin_files\OnOffClusterFsm_20251209_052837.spthy", "--parse"],
    capture_output=True,
    text=True,
    timeout=60
)

print("Result:")
print(result)
