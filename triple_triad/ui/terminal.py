"""The single shared blessed Terminal instance for the whole app.

Import ``term`` from here instead of constructing new ``Terminal()``
objects — multiple instances waste capability queries and can disagree
about terminal state.
"""

from blessed import Terminal

term = Terminal()
