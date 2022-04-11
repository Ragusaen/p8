import os

git_url = "https://git.overleaf.com/621f414465d506ef93365643"


def synchronize():
    if not os.path.exists('overleaf'):
        os.system(f"git clone {git_url} overleaf")
    else:
        os.system("cd overleaf; git stash; git pull --rebase; cd ..")

def set_file_text(text: str, fname: str):
    synchronize()
    with open(f"overleaf/{fname}", "w") as file:
        file.write(text)
    os.system(f"cd overleaf; git add {fname}; git commit {fname} -m \"updated plots\"; git push -f; cd ..")