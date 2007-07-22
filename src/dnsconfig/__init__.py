from dnsconfig import DnsConfig
from optparse import OptionParser
import os, sys

parser = OptionParser()
parser.add_option('-c', '--config', dest='config', help='use FILE as the config file', metavar='FILE')
parser.add_option('-f', '--force', dest='force', help='force reloading all zones and config files', action="store_true")
parser.set_defaults(config='/etc/dnsconfig.conf')

(options, args) = parser.parse_args()

if (not os.path.exists(options.config)):
    sys.stderr.write("Config %(file)s not found.\n" % { 'file' : options.config })
    sys.exit(1)

try:
    dnsconfig = DnsConfig(options.config, options.force)
    dnsconfig.execute()
except Exception, exp:
    sys.stderr.write("An error occurred: %s\n" % exp)
    sys.exit(1)