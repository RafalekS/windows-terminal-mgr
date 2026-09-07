"""Windows Terminal Manager - application modules.

The package is split by functionality:

- ``app_state``          shared mutable state (settings.json data, derived lists,
                         save/backup, UID stamping) and the ``--debug`` flag
- ``config``             application config (config/settings.json)
- ``themes``             theme colour loading and the Qt stylesheet builder
- ``constants``          Windows Terminal action names / enum option lists
- ``widgets``            reusable Qt widget subclasses (CommandStep, tree, key recorder)
- ``main_window``        ``Ui_MainWindow`` - composes the tab mixins
- ``*_tab``              one mixin class per tab (profiles, folders, actions,
                         command_builder, settings, fragments)

Shared mutable state lives in ``app_state`` / ``config`` / ``themes`` as *module
attributes*. Import the module and read ``module.name`` - never
``from app_state import data_schemes`` - so runtime reassignments are visible
everywhere.
"""
