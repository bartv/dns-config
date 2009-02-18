from setuptools import setup, find_packages

setup(
        name = "dns-config",
        version = "0.6",
        packages = find_packages('src'),
        package_dir = {'':'src'},
        description = "Tool to generate dns configuration from ldap",
        license = "MIT",

        author = "Bart Vanbrabant",
        author_email = "bart@vanbrabant.eu",
        url = "http://bart.ulyssis.org/hg/dns-config",

        entry_points = { 
            'console_scripts' : ['dnsconfig = dnsconfig:main']
        }
)
