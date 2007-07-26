from setuptools import setup, find_packages

setup(
        name = "dns-config",
        version = "0.3",
        packages = find_packages('src'),
        package_dir = {'':'src'},

        author = "Bart Vanbrabant",
        author_email = "bart.vanbrabant@zoeloelip.be",
        url = "http://bart.ulyssis.org/hg/dns-config",
)
