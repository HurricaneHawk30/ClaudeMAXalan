"""Subject modules for the tutor engine.

Every public module here (name not starting with ``_``) is imported by
``tutor.content.load_registry()`` and must define ``register(reg)``, which calls
``reg.register(Subject(...), [Skill(...), ...])``.  Adding a subject = adding one file.
"""
