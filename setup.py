from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel


class PlatformWheel(bdist_wheel):
    """Mark wheels as platform-specific because native libraries are packaged."""

    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False


setup(cmdclass={"bdist_wheel": PlatformWheel})
