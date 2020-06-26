"""
Hook for setuptools/distutils
"""

import setuptools.dist

from setupmeta.model import MetaDefs, SetupMeta


finalize_options_orig = setuptools.dist.Distribution.finalize_options
def finalize_options(dist):
    """
    Hook into setuptools' Distribution class before attributes are interpreted.

    This is called before Distribution attributes are finalized and validated,
    allowing us to transform attribute values before they have to conform to
    the usual spec. This step is *before* configuration is additionally read
    from config files.
    """
    dist._setupmeta = SetupMeta()
    MetaDefs.fill_dist(dist, dist._setupmeta.preprocess(dist).to_dict())
    finalize_options_orig(dist)


parse_config_files_orig = setuptools.dist.Distribution.parse_config_files
def parse_config_files(dist, filenames=None, ignore_option_errors=False):
    """
    Hook into setuptools' Distribution class during final configuration phases.

    This allows us to insert setupmeta's imputed values for various attributes
    after all configuration has interpreted and read from config files.
    """
    parse_config_files_orig(dist, filenames=filenames, ignore_option_errors=ignore_option_errors)
    if hasattr(dist, '_setupmeta'):  # This will not be true during installation of setup requirements.
        MetaDefs.fill_dist(dist, dist._setupmeta.finalize(dist).to_dict())


def register(dist, name, value):
    """ Hook into distutils in order to do our magic

    We use this as a 'distutils.setup_keywords' entry point
    We don't need to do anything specific here (in this function)
    But we do need distutils to import this module
    """
    if name == "setup_requires":
        value = value if isinstance(value, list) else [value]
        if any(item.startswith('setupmeta') for item in value):
            # Replace Distribution finalization hooks so we can inject our parsed options
            setuptools.dist.Distribution.finalize_options = finalize_options
            setuptools.dist.Distribution.parse_config_files = parse_config_files
        else:
            # Replace Distribution hooks with original implementations (just in case rerunning in same process)
            setuptools.dist.Distribution.finalize_options = finalize_options_orig
            setuptools.dist.Distribution.parse_config_files = parse_config_files_orig
