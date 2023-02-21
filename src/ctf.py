"""
dummy file to trick poetry

See: <https://github.com/python-poetry/poetry/issues/512#issuecomment-430906309>

Quoted:
    @shabbyrobe
    shabbyrobe commented on Oct 18, 2018
    I'm experiencing this too. After reading the source for masonry/utils/module.py, I managed to convince poetry to continue by adding a file to my src directory with the name of my project, i.e. given the pyproject.toml:
    
    [tool.poetry]
    name = "pants"
    I added an empty file called <proj>/src/pants.py, and now I am unblocked.
"""
