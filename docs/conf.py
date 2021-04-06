exec(
    __import__("subprocess").check_output(
        "jb config sphinx --toc _toc.yml --config _config.yml .".split(),
    ), globals(), locals()
)