exec(
    __import__("subprocess").check_output(
        "jb config sphinx --toc docs/_toc.yml --config docs/_config.yml .".split(),
    ), globals(), locals()
)