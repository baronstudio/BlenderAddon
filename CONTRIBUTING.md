# Contributing

Thanks for taking the time to help. Contributions in English or French are both welcome.

## Ways to help

- **Report bugs.** Use the [bug report form](https://github.com/baronstudio/BlenderAddon/issues/new?template=bug_report.yml) and include your Blender version, the add-on version, your OS and the console output.
- **Suggest features.** Use the [feature request form](https://github.com/baronstudio/BlenderAddon/issues/new?template=feature_request.yml).
- **Improve docs.** Fix typos, add screenshots, or translate a README.
- **Send code.** Open a pull request; see below.

## Development setup

1. Fork and clone the repository.
2. Link the add-on folder you are working on into your Blender extensions directory (see the [README](README.md#option-2-for-developers)).
3. Reload scripts in Blender (`F3` → *Reload Scripts*) or restart Blender after changes.
4. Open Blender's system console (*Window → Toggle System Console* on Windows, or launch Blender from a terminal) to see errors.

## Pull request guidelines

- Keep one PR per topic, and keep it small.
- Target the `master` branch.
- Follow the existing code style of the add-on you are editing. Use 4-space indentation and [PEP 8](https://peps.python.org/pep-0008/) where practical.
- Prefix new Blender classes the way the add-on already does (`T4A_OT_…`, `T4A_PT_…`, and so on).
- Look up shader nodes by `type`, never by name, because names are localized.
- Don't commit `__pycache__/`, `*.blend1` or personal editor settings.
- Don't commit large `.blend` files unless they are needed for a test. Keep test scenes small and free of third-party or client content.
- Describe how you tested the change and which Blender version you used.
- Update the add-on's README or CHANGELOG when behavior changes.

## License of contributions

By submitting a contribution, you agree that it is licensed under the [GPL-3.0-or-later](LICENSE), the license of this project.
